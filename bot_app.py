# bot_app.py

import os
import logging
import asyncio
from geopy.exc import GeocoderTimedOut
from flask import Flask, request, jsonify 
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes
)
# فرض می‌شود geopy از قبل نصب و ایمپورت شده است

# --------------------------------------------------
# تنظیمات اولیه و متغیرهای محیطی
# --------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# تعریف متغیرهای محیطی
# حتماً این متغیرها را در تنظیمات Render ست کنید
TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_DEFAULT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "YOUR_DEFAULT_URL")
PORT = int(os.environ.get("PORT", 8080))

# تعریف حالات ConversationHandler
DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)

# --------------------------------------------------
# توابع کمکی (Async to Sync Helpers)
# --------------------------------------------------

# این توابع باید منطق همزمان شما را اجرا کنند (مثل geopy)
def normalize_digits(text):
    # منطق نرمال‌سازی ارقام فارسی/عربی به انگلیسی در اینجا
    return text.strip()

def _run_geocode_sync(city_name):
    # این تابع منطق geopy را اجرا می‌کند
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="telegram_bot")
    return geolocator.geocode(city_name, timeout=10)

def _run_horoscope_sync(data):
    # این تابع منطق اصلی محاسبات شما را اجرا می‌کند
    return "متن پیش‌فرض طالع‌بینی", None

def get_healing_text():
    return "متن شفابخشی پیش‌فرض" 

# --------------------------------------------------
# توابع هندلر (Async Handlers)
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("خوش آمدید! از منوی زیر انتخاب کنید.")
    elif update.callback_query:
         await context.bot.send_message(chat_id=update.effective_chat.id, text="خوش آمدید! از منوی زیر انتخاب کنید.")

async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("لطفا عدد صحیح برای **روز** تولد (مثلاً: 15) وارد کنید: 📅")
    return DAY

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = normalize_digits(update.message.text)
        context.user_data['day'] = int(text) if text.isdigit() else 0
        await update.message.reply_text("لطفا عدد صحیح برای **ماه** تولد (مثلاً: 10) وارد کنید: 🗓️")
        return MONTH
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **روز** وارد کنید:")
        return DAY

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = normalize_digits(update.message.text)
        context.user_data['month'] = int(text) if text.isdigit() else 0
        await update.message.reply_text("لطفا عدد صحیح برای **سال** تولد (مثلاً: 1370) وارد کنید: 🎂")
        return YEAR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **ماه** وارد کنید:")
        return MONTH

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = normalize_digits(update.message.text)
        context.user_data['year'] = int(text) if text.isdigit() else 0
        await update.message.reply_text("لطفا عدد صحیح برای **ساعت** وارد کنید:")
        return HOUR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **سال** وارد کنید:")
        return YEAR

async def get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = normalize_digits(update.message.text)
        context.user_data['hour'] = int(text) if text.isdigit() else 0
        await update.message.reply_text("لطفا عدد صحیح برای **دقیقه** وارد کنید:")
        return MINUTE
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **ساعت** وارد کنید:")
        return HOUR

async def get_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = normalize_digits(update.message.text)
        context.user_data['minute'] = int(text) if text.isdigit() else 0
        await update.message.reply_text("لطفاً نام شهر یا مکان تولد خود را وارد کنید (مثلاً: تهران) 🗺️")
        return CITY
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **دقیقه** وارد کنید:")
        return MINUTE


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_name = update.message.text.strip()
    await update.message.reply_text("در حال پردازش درخواست شما... لطفاً صبر کنید. ⏳")
    
    try:
        location = await asyncio.to_thread(_run_geocode_sync, city_name) 

        if location:
            context.user_data['lat'] = location.latitude
            context.user_data['lon'] = location.longitude

            data = context.user_data
            
            text, img_path = await asyncio.to_thread(_run_horoscope_sync, data)
            
            if img_path and os.path.exists(img_path):
                 await update.message.reply_photo(photo=open(img_path, 'rb'), caption=text)
            else:
                 await update.message.reply_text(text)
            
            return ConversationHandler.END
        else:
            await update.message.reply_text("شهر پیدا نشد. لطفاً نام شهر را دقیق وارد کنید.")
            return CITY
    
    except GeocoderTimedOut:
        logging.error("Geocoder Timed Out")
        await update.message.reply_text("خطا در اتصال به سرویس موقعیت‌یابی، دوباره تلاش کنید.")
        return CITY
    except Exception as e:
        logging.error(f"Error in get_city (Final stage error): {e}")
        await update.message.reply_text("خطایی رخ داد. لطفاً مطمئن شوید اطلاعات ورودی معتبر هستند.")
        return CITY

async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_healing_text()
    await query.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context) 
    return ConversationHandler.END


# ----------------- Dispatcher / Application -----------------

# **** اصلاح حیاتی: حذف .rate_limiter(1) برای حل خطای AttributeError ****
app_bot = ApplicationBuilder().token(TOKEN).build()

horoscope_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(horoscope_start, pattern='^horoscope$')],
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

# اضافه کردن هندلرها
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(horoscope_conv)
app_bot.add_handler(CallbackQueryHandler(healing_start, pattern='^healing$'))
app_bot.add_handler(CallbackQueryHandler(start, pattern='^intro$|^about$|^shop$|^register$|^chart$'))


# --------------------------------------------------
# توابع Flask و Webhook (اصلاح شده برای Gunicorn WSGI)
# --------------------------------------------------

app = Flask(__name__)

# **** افزودن مسیر ریشه برای Health Check رندر ****
@app.route("/", methods=["GET"])
def home():
    """مسار فحص سلامتی برای Render"""
    return "Bot is running!", 200


# تابع لضبط Webhook بشكل متزامن
def set_webhook_sync():
    """تنظیم وب‌هوک به صورت همزمان با
