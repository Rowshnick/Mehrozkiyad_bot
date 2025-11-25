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

DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)
DATE_CONV_DAY, DATE_CONV_MONTH, DATE_CONV_YEAR = range(100, 103)

geolocator = Nominatim(user_agent="horoscope_bot")

# ----------- Telegram App ---------------
app = ApplicationBuilder().token(TOKEN).build()

# ----------- Flask Web Server ---------------
server = Flask(__name__)


# ------------------- START ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("هوروسکوپ", callback_data='horoscope')],
        [InlineKeyboardButton("هیولینگ", callback_data='healing')],
        [InlineKeyboardButton("تبدیل تاریخ", callback_data='date_conv')],
        [InlineKeyboardButton("درباره ما", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام! من بات حرفه‌ای هستم. یکی از گزینه‌ها را انتخاب کنید:", 
        reply_markup=reply_markup
    )


# ------------------- HOROSCOPE ---------------------
async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("روز تولد؟")
    return DAY


async def get_day(update, context):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("ماه تولد؟")
    return MONTH


async def get_month(update, context):
    context.user_data['month'] = int(update.message.text)
    await update.message.reply_text("سال تولد؟")
    return YEAR


async def get_year(update, context):
    context.user_data['year'] = int(update.message.text)
    await update.message.reply_text("ساعت تولد (نداری؟ 12 بزن)")
    return HOUR


async def get_hour(update, context):
    t = update.message.text
    context.user_data['hour'] = int(t) if t.isdigit() else 12
    await update.message.reply_text("دقیقه تولد (نداری؟ 0 بزن)")
    return MINUTE


async def get_minute(update, context):
    t = update.message.text
    context.user_data['minute'] = int(t) if t.isdigit() else 0
    await update.message.reply_text("نام شهر؟")
    return CITY


async def get_city(update, context):
    city = update.message.text.strip()

    try:
        location = geolocator.geocode(city, timeout=10)
        if not location:
            await update.message.reply_text("❌ شهر یافت نشد. نام دقیق‌تری وارد کنید.")
            return CITY

        context.user_data['lat'] = location.latitude
        context.user_data['lon'] = location.longitude

        data = context.user_data
        text, img_path = get_horoscope_with_image(
            year=data['year'], month=data['month'], day=data['day'],
            hour=data['hour'], minute=data['minute'],
            lat=data['lat'], lon=data['lon']
        )

        await update.message.reply_photo(
            photo=open(img_path, 'rb'),
            caption=text
        )
        return ConversationHandler.END

    except GeocoderTimedOut:
        await update.message.reply_text("⏳ خطای اتصال. دوباره تلاش کنید.")
        return CITY


# ------------------- HEALING ---------------------
async def healing_start(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(get_healing_text())
    return ConversationHandler.END


# ------------------- DATE CONVERSION ---------------------
async def date_conv_start(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("روز؟")
    return DATE_CONV_DAY


async def date_conv_day(update, context):
    context.user_data['day_conv'] = int(update.message.text)
    await update.message.reply_text("ماه؟")
    return DATE_CONV_MONTH


async def date_conv_month(update, context):
    context.user_data['month_conv'] = int(update.message.text)
    await update.message.reply_text("سال؟")
    return DATE_CONV_YEAR


async def date_conv_year(update, context):
    y = int(update.message.text)
    m = context.user_data['month_conv']
    d = context.user_data['day_conv']

    try:
        jalali = JalaliDate(y, m, d).to_jalali()
        await update.message.reply_text(
            f"شمسی: {jalali.year}/{jalali.month}/{jalali.day}\n"
            f"میلادی: {y}/{m}/{d}"
        )
    except:
        await update.message.reply_text("❌ خطا. دوباره تلاش کنید.")

    return ConversationHandler.END


# ------------------- ABOUT ---------------------
async def about(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "این بات توسط Roshina Nikzad توسعه داده شده است."
    )


# ------------------- FLASK WEBHOOK ENDPOINT ---------------------
@server.post("/")
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.update_queue.put_nowait(update)
    return "OK", 200


def set_webhook():
    url = os.getenv("RENDER_EXTERNAL_URL")
    webhook_url = f"{url}/"

    import requests
    requests.get(
        f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
    )
    print("Webhook Set:", webhook_url)


# ------------------- MAIN ---------------------
if __name__ == "__main__":
    # ثبت تمامی هندلرها
    app.add_handler(CommandHandler("start", start))

    # Horoscope conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(horoscope_start, pattern='horoscope')],
        states={
            DAY: [MessageHandler(filters.TEXT, get_day)],
            MONTH: [MessageHandler(filters.TEXT, get_month)],
            YEAR: [MessageHandler(filters.TEXT, get_year)],
            HOUR: [MessageHandler(filters.TEXT, get_hour)],
            MINUTE: [MessageHandler(filters.TEXT, get_minute)],
            CITY: [MessageHandler(filters.TEXT, get_city)],
        },
        fallbacks=[]
    ))

    # Date conversion conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(date_conv_start, pattern='date_conv')],
        states={
            DATE_CONV_DAY: [MessageHandler(filters.TEXT, date_conv_day)],
            DATE_CONV_MONTH: [MessageHandler(filters.TEXT, date_conv_month)],
            DATE_CONV_YEAR: [MessageHandler(filters.TEXT, date_conv_year)],
        },
        fallbacks=[]
    ))

    app.add_handler(CallbackQueryHandler(healing_start, pattern='healing'))
    app.add_handler(CallbackQueryHandler(about, pattern='about'))

    # فعال‌سازی وب‌هوک
    set_webhook()

    # اجرای وب‌سرور Flask روی پورت Render
    server.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
