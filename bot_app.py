# bot_app.py
import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from utils.horoscope_service import get_horoscope_with_image
from utils.healing_service import get_healing_text
from utils.date_conv import gregorian_to_jalali, jalali_to_gregorian
from utils.hafez_service import get_random_hafez_verse  # ماژول استخراج فال حافظ

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثال: https://mehrozkiyad-bot.onrender.com

# مراحل دریافت داده‌ها
DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)
DATE_CONV_DAY, DATE_CONV_MONTH, DATE_CONV_YEAR = range(100, 103)

geolocator = Nominatim(user_agent="horoscope_bot")

# --- Flask App ---
app = Flask(__name__)

# --- استارت و منو ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("هوروسکوپ (ستاره شناسی)", callback_data='horoscope')],
        [InlineKeyboardButton("درمان (هیولینگ)", callback_data='healing')],
        [InlineKeyboardButton("چارت تولد (ستاره شناسی)", callback_data='chart')],
        [InlineKeyboardButton("فروشگاه محصولات درمانی", callback_data='shop')],
        [InlineKeyboardButton("عضویت در ربات", callback_data='register')],
        [InlineKeyboardButton("فال حافظ", callback_data='hafez')],
        [InlineKeyboardButton("درباره ما", callback_data='about')],
        [InlineKeyboardButton("معرفی ربات", callback_data='intro')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            "سلام! من بات حرفه‌ای هستم. یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "سلام! من بات حرفه‌ای هستم. یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup
        )

# --- هوروسکوپ ---
async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("لطفاً روز تولد خود را وارد کنید (مثلاً: 17)")
    return DAY

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("ماه تولد خود را وارد کنید (مثلاً: 5)")
    return MONTH

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = int(update.message.text)
    await update.message.reply_text("سال تولد خود را وارد کنید (مثلاً: 1990)")
    return YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = int(update.message.text)
    await update.message.reply_text("ساعت تولد (اختیاری، اگر ندارید 12 وارد کنید)")
    return HOUR

async def get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['hour'] = int(text) if text.isdigit() else 12
    await update.message.reply_text("دقیقه تولد (اختیاری، اگر ندارید 0 وارد کنید)")
    return MINUTE

async def get_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['minute'] = int(text) if text.isdigit() else 0
    await update.message.reply_text("لطفاً نام شهر یا مکان تولد خود را وارد کنید (مثلاً: تهران)")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_name = update.message.text.strip()
    try:
        location = geolocator.geocode(city_name, timeout=10)
        if location:
            context.user_data['lat'] = location.latitude
            context.user_data['lon'] = location.longitude

            data = context.user_data
            text, img_path = get_horoscope_with_image(
                year=data['year'], month=data['month'], day=data['day'],
                hour=data['hour'], minute=data['minute'],
                lat=data['lat'], lon=data['lon']
            )
            await update.message.reply_photo(photo=open(img_path, 'rb'), caption=text)
            return ConversationHandler.END
        else:
            await update.message.reply_text("شهر وارد شده پیدا نشد. لطفاً نام شهر را دقیق وارد کنید.")
            return CITY
    except GeocoderTimedOut:
        await update.message.reply_text("خطا در اتصال به سرویس موقعیت‌یابی، دوباره تلاش کنید.")
        return CITY

# --- درمان (هیولینگ) ---
async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = get_healing_text()
    await update.callback_query.message.reply_text(text)
    return ConversationHandler.END

# --- فال حافظ ---
async def hafez_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    verse = get_random_hafez_verse()
    await update.callback_query.message.reply_text(f"فال حافظ شما:\n\n{verse}")
    return ConversationHandler.END

# --- لغو ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# --- ConversationHandlers ---
horoscope_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(horoscope_start, pattern='horoscope')],
    states={
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
        MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_month)],
        YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
        HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hour)],
        MINUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_minute)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

# --- Dispatcher / Application ---
app_bot = ApplicationBuilder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(horoscope_conv)
app_bot.add_handler(CallbackQueryHandler(healing_start, pattern='healing'))
app_bot.add_handler(CallbackQueryHandler(hafez_start, pattern='hafez'))

# --- Flask route for webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    from telegram import Update
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    app_bot.update_queue.put(update)
    return "ok"

# --- Run bot ---
if __name__ == "__main__":
    # Set webhook
    app_bot.bot.delete_webhook()
    app_bot.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
