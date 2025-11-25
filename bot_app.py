import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Dispatcher, CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from utils.horoscope_service import get_horoscope_with_image
from utils.healing_service import get_healing_text
from utils.date_conv import gregorian_to_jalali, jalali_to_gregorian
from utils.divan_hafez import get_random_hafez

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)
DATE_CONV_DAY, DATE_CONV_MONTH, DATE_CONV_YEAR = range(100, 103)

geolocator = Nominatim(user_agent="mehrozkiyad_bot")

app = Flask(__name__)
bot = Bot(TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# استارت / منوی اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ستاره‌شناسی", callback_data='horoscope')],
        [InlineKeyboardButton("درمان", callback_data='healing')],
        [InlineKeyboardButton("چارت تولد", callback_data='birth_chart')],
        [InlineKeyboardButton("فروشگاه درمانی", callback_data='shop')],
        [InlineKeyboardButton("عضویت در ربات", callback_data='membership')],
        [InlineKeyboardButton("درباره ما", callback_data='about')],
        [InlineKeyboardButton("معرفی ربات", callback_data='intro')],
        [InlineKeyboardButton("تفال دیوان حافظ", callback_data='hafez')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("سلام! لطفاً گزینه‌ای را انتخاب کن:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("سلام! لطفاً گزینه‌ای را انتخاب کن:", reply_markup=reply_markup)

# — ستاره‌شناسی (هوروسکوپ) —
async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("روز تولد را وارد کن (مثال: 17)")
    return DAY

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("ماه تولد را وارد کن (مثال: 5)")
    return MONTH

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = int(update.message.text)
    await update.message.reply_text("سال تولد را وارد کن (مثال: 1990)")
    return YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = int(update.message.text)
    await update.message.reply_text("ساعت تولد (اگر نمی‌دانی، 12 وارد کن):")
    return HOUR

async def get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    context.user_data['hour'] = int(t) if t.isdigit() else 12
    await update.message.reply_text("دقیقه تولد (اگر ندارید، 0):")
    return MINUTE

async def get_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    context.user_data['minute'] = int(t) if t.isdigit() else 0
    await update.message.reply_text("نام شهر تولد را وارد کن (مثال: تهران):")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_name = update.message.text.strip()
    try:
        loc = geolocator.geocode(city_name, timeout=10)
        if not loc:
            await update.message.reply_text("شهر پیدا نشد، لطفاً دقیقاً بنویس.")
            return CITY
        context.user_data['lat'] = loc.latitude
        context.user_data['lon'] = loc.longitude

        data = context.user_data
        text, img = get_horoscope_with_image(
            year=data['year'], month=data['month'], day=data['day'],
            hour=data['hour'], minute=data['minute'],
            lat=data['lat'], lon=data['lon']
        )
        await update.message.reply_photo(photo=open(img, 'rb'), caption=text)
        return ConversationHandler.END

    except GeocoderTimedOut:
        await update.message.reply_text("خطا در موقعیت‌یابی، دوباره تلاش کن.")
        return CITY

# — درمان —
async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("سنگ درمانی", callback_data='stone')],
        [InlineKeyboardButton("گیاه درمانی", callback_data='herb')],
        [InlineKeyboardButton("مانترا درمانی", callback_data='mantra')],
        [InlineKeyboardButton("نماد درمانی", callback_data='symbol')],
        [InlineKeyboardButton("بازگشت", callback_data='back')]
    ]
    await update.callback_query.message.reply_text("نوع درمان را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

async def healing_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    choice = update.callback_query.data
    text = get_healing_text()
    await update.callback_query.message.reply_text(f"🔹 {choice}:\n{text}")
    return ConversationHandler.END

# — تفال حافظ —
async def hafez_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    poem = get_random_hafez()
    await update.callback_query.message.reply_text(f"🌸 حافظ:\n\n{poem}")

# — تولد چارت —  
# (می‌توان مشابه هوروسکوپ، اما فقط موقعیت دقیق تولد بدون تحلیل پیچیده)
async def birth_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("برای چارت تولد، لطفاً روز تولد خود را وارد کن:")
    return DAY

async def birth_get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = int(update.message.text)
    await update.message.reply_text("ماه تولد را وارد کن:")
    return MONTH

async def birth_get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = int(update.message.text)
    await update.message.reply_text("سال تولد را وارد کن:")
    return YEAR

async def birth_get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = int(update.message.text)
    await update.message.reply_text("ساعت تولد (اگر نمی‌دانی، 12 بزن):")
    return HOUR

async def birth_get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    context.user_data['hour'] = int(t) if t.isdigit() else 12
    await update.message.reply_text("دقیقه تولد (اگر ندارید، 0):")
    return MINUTE

async def birth_get_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    context.user_data['minute'] = int(t) if t.isdigit() else 0
    await update.message.reply_text("نام شهر تولد را وارد کن:")
    return CITY

async def birth_get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_name = update.message.text.strip()
    try:
        loc = geolocator.geocode(city_name, timeout=10)
        if not loc:
            await update.message.reply_text("شهر پیدا نشد، دوباره وارد کن.")
            return CITY
        data = context.user_data
        lat, lon = loc.latitude, loc.longitude
        text, img = get_horoscope_with_image(
            year=data['year'], month=data['month'], day=data['day'],
            hour=data['hour'], minute=data['minute'],
            lat=lat, lon=lon
        )
        # در تولد چارت، فقط تصویر و مختصات را نشان بده
        await update.message.reply_photo(photo=open(img, 'rb'), caption=f"چارت تولد شما:\n{text}")
        return ConversationHandler.END
    except GeocoderTimedOut:
        await update.message.reply_text("خطا، دوباره تلاش کن.")
        return CITY

# — درباره ما —
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "تیم توسعه: Roshina Nikzad\nاین ربات شامل خدمات ستاره‌شناسی، درمان انرژی، تفال حافظ و چارت تولد است."
    await update.callback_query.message.reply_text(text)

# — معرفی ربات —
async def intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "ربات Mehrozkiyad: ترکیب هنر ستاره‌شناسی و روش‌های درمانی با تفال حافظ برای الهام‌بخشی در زندگی."
    await update.callback_query.message.reply_text(text)

# — لغو —
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# Conversation Handlerها
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
    per_message=False
)

healing_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(healing_start, pattern='healing')],
    states={
        'CHOICE': [CallbackQueryHandler(healing_choice, pattern='^(stone|herb|mantra|symbol)$')]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    per_message=False
)

birth_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(birth_chart, pattern='birth_chart')],
    states={
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_get_day)],
        MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_get_month)],
        YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_get_year)],
        HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_get_hour)],
        MINUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_get_minute)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_get_city)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    per_message=False
)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(horoscope_conv)
dispatcher.add_handler(healing_conv)
dispatcher.add_handler(birth_conv)
dispatcher.add_handler(CallbackQueryHandler(hafez_start, pattern='hafez'))
dispatcher.add_handler(CallbackQueryHandler(about, pattern='about'))
dispatcher.add_handler(CallbackQueryHandler(intro, pattern='intro'))

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    bot.delete_webhook()
    bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
