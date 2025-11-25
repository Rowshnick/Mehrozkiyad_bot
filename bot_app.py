import os
from datetime import datetime
import swisseph as swe
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
from dotenv import load_dotenv
import pytz
import requests
from persiantools.jdatetime import JalaliDate

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
print("TOKEN:", TOKEN)  # برای تست مقدار Token

if not TOKEN:
    raise ValueError("توکن تلگرام تنظیم نشده است! لطفاً در Environment Variable با کلید BOT_TOKEN مقداردهی کنید.")

# حالت‌ها برای ConversationHandler
SELECT_LANGUAGE, GET_BIRTHDATE, SHOW_HOROSCOPE = range(3)

# متغیرهای بینابینی
user_data_store = {}

# دکمه‌های زبان
LANG_KEYBOARD = [
    [InlineKeyboardButton("فارسی", callback_data="fa")],
    [InlineKeyboardButton("English", callback_data="en")]
]

def generate_date_keyboard(lang="fa"):
    if lang == "fa":
        months = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"]
    else:
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_buttons = [[InlineKeyboardButton(m, callback_data=str(i+1))] for i, m in enumerate(months)]
    day_buttons = [[InlineKeyboardButton(str(d), callback_data=str(d))] for d in range(1, 32)]
    year_buttons = [[InlineKeyboardButton(str(y), callback_data=str(y))] for y in range(1950, 2026)]
    return month_buttons, day_buttons, year_buttons

def generate_horoscope_text(birth_date: datetime, lang="fa") -> str:
    jd = swe.julday(birth_date.year, birth_date.month, birth_date.day)
    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO
    }
    horoscope = ""
    for name, code in planets.items():
        lon, lat, dist = swe.calc(jd, code)[:3]
        horoscope += f"{name}: Longitude={lon:.2f}, Latitude={lat:.2f}\n"
    horoscope += "\nپیشنهاد: امروز تمرکز روی خودشناسی و تقویت روابطتان باشد.\n" if lang=="fa" else "\nSuggestion: Focus on self-awareness and strengthening your relationships today.\n"
    return horoscope

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(LANG_KEYBOARD)
    await update.message.reply_text("لطفاً زبان خود را انتخاب کنید / Please select your language:", reply_markup=keyboard)
    return SELECT_LANGUAGE

async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    user_data_store[query.from_user.id] = {"lang": lang}
    await query.message.reply_text(f"زبان انتخاب شد: {lang}")
    return GET_BIRTHDATE

async def get_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        birth_date = datetime.strptime(text, "%Y-%m-%d")
        user_data_store[update.message.from_user.id]["birth_date"] = birth_date
        horoscope = generate_horoscope_text(birth_date, user_data_store[update.message.from_user.id]["lang"])
        await update.message.reply_text(horoscope)
    except Exception as e:
        await update.message.reply_text("فرمت تاریخ اشتباه است. لطفاً YYYY-MM-DD وارد کنید.")
    return SHOW_HOROSCOPE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        SELECT_LANGUAGE: [CallbackQueryHandler(language_choice)],
        GET_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthdate)],
        SHOW_HOROSCOPE: []
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

app.add_handler(conv_handler)

if __name__ == "__main__":
    print("Bot is starting with webhook...")
    PORT = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://mehrozkiyad-bot.onrender.com/{TOKEN}"
    )

