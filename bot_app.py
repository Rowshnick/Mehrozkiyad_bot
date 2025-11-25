import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from persiantools.jdatetime import JalaliDate

from utils.horoscope_service import get_horoscope_with_image
from utils.healing_service import get_healing_text

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # در Render قرار بده: https://your-app.onrender.com/webhook

app = Flask(__name__)

# مراحل
DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)
DATE_CONV_DAY, DATE_CONV_MONTH, DATE_CONV_YEAR = range(100, 103)

geolocator = Nominatim(user_agent="horoscope_bot")

telegram_app = ApplicationBuilder().token(TOKEN).build()


# ---------------------------
#       BOT HANDLERS
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("هوروسکوپ", callback_data='horoscope')],
        [InlineKeyboardButton("هیولینگ", callback_data='healing')],
        [InlineKeyboardButton("تبدیل تاریخ", callback_data='date_conv')],
        [InlineKeyboardButton("درباره ما", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام! من بات حرفه‌ای هستم. یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup
    )


# --- هوروسکوپ ---
async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("لطفاً روز تولد خود را وارد کنید:")
    return DAY


async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("ماه تولد را وارد کنید:")
    return MONTH


async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = int(update.message.text)
    await update.message.reply_text("سال تولد:")
    return YEAR


async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = int(update.message.text)
    await update.message.reply_text("ساعت تولد (اگر ندارید 12):")
    return HOUR


async def get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    context.user_data['hour'] = int(t) if t.isdigit() else 12
    await update.message.reply_text("دقیقه تولد (اگر ندارید 0):")
    return MINUTE


async def get_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    context.user_data['minute'] = int(t) if t.isdigit() else 0
    await update.message.reply_text("نام شهر محل تولد:")
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    try:
        location = geolocator.geocode(city, timeout=10)
        if not location:
            await update.message.reply_text("شهر پیدا نشد! دوباره دقیق‌تر وارد کنید.")
            return CITY

        context.user_data['lat'] = location.latitude
        context.user_data['lon'] = location.longitude

        d = context.user_data
        text, img = get_horoscope_with_image(
            year=d['year'], month=d['month'], day=d['day'],
            hour=d['hour'], minute=d['minute'],
            lat=d['lat'], lon=d['lon']
        )
        await update.message.reply_photo(photo=open(img, 'rb'), caption=text)
        return ConversationHandler.END

    except GeocoderTimedOut:
        await update.message.reply_text("خطا در سرویس موقعیت‌یابی. دوباره تلاش کنید.")
        return CITY


# --- هیولینگ ---
async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(get_healing_text())
    return ConversationHandler.END


# --- تبدیل تاریخ ---
async def date_conv_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("روز:")
    return DATE_CONV_DAY


async def date_conv_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d'] = int(update.message.text)
    await update.message.reply_text("ماه:")
    return DATE_CONV_MONTH


async def date_conv_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['m'] = int(update.message.text)
    await update.message.reply_text("سال:")
    return DATE_CONV_YEAR


async def date_conv_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    y = int(update.message.text)
    m = context.user_data['m']
    d = context.user_data['d']

    try:
        j = JalaliDate(y, m, d).to_jalali()
        await update.message.reply_text(f"📅 شمسی: {j.year}/{j.month}/{j.day}")
    except:
        await update.message.reply_text("خطا در تبدیل. روز را وارد کنید:")
        return DATE_CONV_DAY

    return ConversationHandler.END


# ---------------------------
#      INTERNAL FLASK APP
# ---------------------------

@app.route("/", methods=["GET"])
def home():
    return "Bot is running."


@app.route("/webhook", methods=["POST"])
def webhook():
    json_update = request.get_json()
    update = Update.de_json(json_update, telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200


# ------------------------------------------------------------
#                SET WEBHOOK & RUN SERVER
# ------------------------------------------------------------

def setup_bot():
    # Handlers
    telegram_app.add_handler(CommandHandler("start", start))

    # Horoscope handler
    horoscope_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(horoscope_start, pattern="horoscope")],
        states={
            DAY: [MessageHandler(filters.TEXT, get_day)],
            MONTH: [MessageHandler(filters.TEXT, get_month)],
            YEAR: [MessageHandler(filters.TEXT, get_year)],
            HOUR: [MessageHandler(filters.TEXT, get_hour)],
            MINUTE: [MessageHandler(filters.TEXT, get_minute)],
            CITY: [MessageHandler(filters.TEXT, get_city)],
        },
        fallbacks=[]
    )
    telegram_app.add_handler(horoscope_conv)

    # Date converter
    date_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(date_conv_start, pattern="date_conv")],
        states={
            DATE_CONV_DAY: [MessageHandler(filters.TEXT, date_conv_day)],
            DATE_CONV_MONTH: [MessageHandler(filters.TEXT, date_conv_month)],
            DATE_CONV_YEAR: [MessageHandler(filters.TEXT, date_conv_year)],
        },
        fallbacks=[]
    )
    telegram_app.add_handler(date_conv)

    telegram_app.add_handler(CallbackQueryHandler(healing_start, pattern="healing"))
    telegram_app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.message.reply_text(
        "تیم توسعه: Roshina Nikzad\nاین بات خدمات حرفه‌ای ارائه می‌دهد."
    ), pattern="about"))

    # Set webhook
    telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    print("Webhook set:", WEBHOOK_URL)


if __name__ == "__main__":
    setup_bot()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)













