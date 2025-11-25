import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)
from utils import astro, healing, date_converter, image_gen, payment, referral
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# مراحل گفتگو
(
    MAIN_MENU,
    HOROSCOPE_DAY,
    HOROSCOPE_MONTH,
    HOROSCOPE_YEAR,
    HEALING,
    DATE_CONVERT,
    PAYMENT,
) = range(7)

# منوی اصلی
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("هوروسکوپ 🪐", callback_data="horoscope")],
        [InlineKeyboardButton("هیولینگ ✨", callback_data="healing")],
        [InlineKeyboardButton("تبدیل تاریخ 📅", callback_data="date_convert")],
        [InlineKeyboardButton("درباره ما ℹ️", callback_data="about")],
        [InlineKeyboardButton("شبکه اجتماعی 🌐", url="https://yourwebsite.com")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به بوت حرفه‌ای مهروزکیاد خوش آمدید! 🌟\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کنید:", 
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU

# هندلر انتخاب منو
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "horoscope":
        await query.message.reply_text("لطفاً روز تولد خود را وارد کنید (عدد):")
        return HOROSCOPE_DAY
    elif data == "healing":
        await query.message.reply_text("لطفاً موضوع هیولینگ خود را وارد کنید:")
        return HEALING
    elif data == "date_convert":
        await query.message.reply_text("لطفاً تاریخ خود را وارد کنید (YYYY-MM-DD):")
        return DATE_CONVERT
    elif data == "about":
        await query.message.reply_text(
            "بوت حرفه‌ای مهروزکیاد توسط تیم ما ساخته شده است.\n"
            "وب‌سایت: https://yourwebsite.com\n"
            "اینستاگرام: https://instagram.com/yourprofile"
        )
        return MAIN_MENU

# جمع‌آوری روز/ماه/سال و تولید هوروسکوپ
async def horoscope_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("لطفاً ماه تولد خود را وارد کنید (عدد):")
    return HOROSCOPE_MONTH

async def horoscope_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = int(update.message.text)
    await update.message.reply_text("لطفاً سال تولد خود را وارد کنید (عدد):")
    return HOROSCOPE_YEAR

async def horoscope_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = int(update.message.text)
    day = context.user_data['day']
    month = context.user_data['month']
    year = context.user_data['year']

    text = astro.get_horoscope(day, month, year)
    img_path = image_gen.create_horoscope_image(day, month, year)

    await update.message.reply_photo(photo=open(img_path, 'rb'), caption=text)
    return MAIN_MENU

# هیولینگ
async def healing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    response = healing.generate_healing(topic)
    await update.message.reply_text(response)
    return MAIN_MENU

# تبدیل تاریخ
async def date_convert_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text
    converted = date_converter.convert_date(date_str)
    await update.message.reply_text(f"تبدیل تاریخ:\n{converted}")
    return MAIN_MENU

# برنامه اصلی
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        MAIN_MENU: [CallbackQueryHandler(menu_handler)],
        HOROSCOPE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_day)],
        HOROSCOPE_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_month)],
        HOROSCOPE_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_year)],
        HEALING: [MessageHandler(filters.TEXT & ~filters.COMMAND, healing_handler)],
        DATE_CONVERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_convert_handler)],
    },
    fallbacks=[CommandHandler("start", start)],
)

app.add_handler(conv_handler)

if __name__ == "__main__":
    print("بوت در حال اجراست...")
    app.run_polling()
