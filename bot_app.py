import os
import logging
from datetime import datetime
import sqlite3

from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
    Update
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    CallbackQueryHandler, ConversationHandler, filters
)

from utils import astro, healing, date_conv, image_gen, payment

# ----- Logging -----
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----- Database -----
DB_PATH = "data/bot_data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    referral TEXT,
    paid INTEGER DEFAULT 0
)
""")
conn.commit()

# ----- States -----
DAY, MONTH, YEAR = range(3)
PAYMENT = range(1)

# ----- Main Menu Keyboard -----
main_menu = ReplyKeyboardMarkup(
    [["🪐 هوروسکوپ", "💖 هیولینگ"],
     ["📅 تبدیل تاریخ", "ℹ️ درباره ما"]],
    resize_keyboard=True
)

# ----- Start Command -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    cursor.execute(
        "INSERT OR IGNORE INTO users(user_id, username) VALUES (?, ?)",
        (user.id, user.username)
    )
    conn.commit()
    await update.message.reply_text(
        "سلام! خوش آمدید به بوت حرفه‌ای مهروزکیاد.\n"
        "یک گزینه از منوی زیر انتخاب کنید:",
        reply_markup=main_menu
    )

# ----- Horoscope Conversation -----
async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا روز تولد خود را وارد کنید (عدد):")
    return DAY

async def horoscope_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["day"] = int(update.message.text)
    await update.message.reply_text("ماه تولد خود را وارد کنید (عدد):")
    return MONTH

async def horoscope_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["month"] = int(update.message.text)
    await update.message.reply_text("سال تولد خود را وارد کنید (میلادی):")
    return YEAR

async def horoscope_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["year"] = int(update.message.text)
    day = context.user_data["day"]
    month = context.user_data["month"]
    year = context.user_data["year"]

    text = astro.get_horoscope(day, month, year)
    await update.message.reply_text(f"🪐 هوروسکوپ شما:\n{text}", parse_mode="Markdown")

    # ساخت عکس هوروسکوپ
    image_path = image_gen.create_horoscope_image(day, month, year, text)
    await update.message.reply_photo(open(image_path, "rb"))

    return ConversationHandler.END

# ----- Healing -----
async def healing_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = healing.get_healing_text()
    await update.message.reply_text(text, parse_mode="Markdown")

# ----- Date Conversion -----
async def date_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا تاریخ میلادی خود را وارد کنید (YYYY-MM-DD):")

async def date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text
    try:
        shamsi = date_conv.gregorian_to_jalali(date_str)
        await update.message.reply_text(f"تاریخ شمسی: {shamsi}")
    except:
        await update.message.reply_text("فرمت اشتباه است. دوباره امتحان کنید.")

# ----- About -----
async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "بوت حرفه‌ای مهروزکیاد\n"
        "⚡ نسخه پیشرفته با منو حرفه‌ای و کیبورد چندلایه\n"
        "💻 پشتیبانی هوروسکوپ، هیولینگ، تبدیل تاریخ\n"
        "🌐 وب‌سایت و شبکه اجتماعی: https://mehrozkiyad.com\n"
    )
    await update.message.reply_text(text)

# ----- Main -----
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation for Horoscope
    horoscope_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("🪐 هوروسکوپ"), horoscope_start)],
        states={
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_day)],
            MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_month)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_year)]
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(horoscope_conv)
    app.add_handler(MessageHandler(filters.Regex("💖 هیولینگ"), healing_cmd))
    app.add_handler(MessageHandler(filters.Regex("📅 تبدیل تاریخ"), date_conversion))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, date_received))
    app.add_handler(MessageHandler(filters.Regex("ℹ️ درباره ما"), about_cmd))

    print("بوت آماده است...")
    app.run_polling()
