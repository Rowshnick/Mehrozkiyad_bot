import os
import logging
import sqlite3
from datetime import datetime
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from utils import astro, healing, date_conv, image_gen, payment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Conversation states
MAIN_MENU, HOROSCOPE_DAY, HOROSCOPE_MONTH, HOROSCOPE_YEAR, HEALING, DATE_CONV = range(6)

# Database initialization
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    referral TEXT,
    paid INTEGER DEFAULT 0
)
""")
conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command and main menu"""
    user = update.effective_user
    keyboard = [
        ["🪐 هوروسکوپ", "💖 هیولینگ"],
        ["📅 تبدیل تاریخ", "ℹ️ درباره ما"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_markdown_v2(
        f"سلام {user.first_name}! 👋\n"
        "به بوت حرفه‌ای مهروزکیاد خوش آمدید.\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=reply_markup
    )
    # Insert user to DB if not exists
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (user.id,))
    conn.commit()
    return MAIN_MENU


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🪐 هوروسکوپ":
        await update.message.reply_text("لطفاً روز تولد خود را وارد کنید (مثال: 21)")
        return HOROSCOPE_DAY
    elif text == "💖 هیولینگ":
        await update.message.reply_text("هیولینگ در حال آماده‌سازی…")
        # Call healing function here
        result = healing.generate_healing(update.effective_user.id)
        await update.message.reply_markdown(result)
        return MAIN_MENU
    elif text == "📅 تبدیل تاریخ":
        await update.message.reply_text("لطفاً تاریخ میلادی خود را وارد کنید (YYYY-MM-DD)")
        return DATE_CONV
    elif text == "ℹ️ درباره ما":
        await update.message.reply_markdown(
            "🤖 بوت حرفه‌ای مهروزکیاد\n"
            "🌐 وب‌سایت: [mehrozkiyad.com](https://mehrozkiyad.com)\n"
            "📱 شبکه اجتماعی: [Instagram](https://instagram.com/mehrozkiyad)"
        )
        return MAIN_MENU
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌ها را از منو انتخاب کنید.")
        return MAIN_MENU


# --- Horoscope flow ---
async def horoscope_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("لطفاً ماه تولد خود را وارد کنید (1-12)")
    return HOROSCOPE_MONTH

async def horoscope_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = int(update.message.text)
    await update.message.reply_text("لطفاً سال تولد خود را وارد کنید (مثال: 1990)")
    return HOROSCOPE_YEAR

async def horoscope_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = int(update.message.text)
    day = context.user_data['day']
    month = context.user_data['month']
    year = context.user_data['year']
    
    # Call astro module to generate horoscope
    result_text = astro.get_horoscope(day, month, year)
    
    # Generate horoscope image
    img_path = image_gen.create_horoscope_image(result_text, update.effective_user.id)
    
    await update.message.reply_photo(photo=open(img_path, 'rb'), caption=result_text, parse_mode="Markdown")
    return MAIN_MENU


# --- Date conversion ---
async def date_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        date_obj = datetime.strptime(text, "%Y-%m-%d")
        shamsi_date = date_conv.gregorian_to_jalali(date_obj)
        await update.message.reply_text(f"تاریخ شمسی: {shamsi_date}")
    except Exception as e:
        await update.message.reply_text("فرمت تاریخ صحیح نیست. لطفاً YYYY-MM-DD وارد کنید.")
    return MAIN_MENU


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            HOROSCOPE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_day)],
            HOROSCOPE_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_month)],
            HOROSCOPE_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_year)],
            DATE_CONV: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_conversion)],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    
    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
    
