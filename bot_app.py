# bot_app.py

import os
import logging
import asyncio # برای اجرای توابع آسنکرون در محیط همزمان
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
    ContextTypes # ایمپورت ContextTypes
)

# --------------------------------------------------
# تنظیمات اولیه و متغیرهای محیطی
# --------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# تعریف متغیرهای محیطی (از os.environ.get استفاده کنید)
TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_DEFAULT_TOKEN") # اطمینان از مقداردهی اولیه
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "YOUR_DEFAULT_URL")
PORT = int(os.environ.get("PORT", 8080)) # پورت برای اجرا محلی

# تعریف حالات ConversationHandler (اگر تعریف نشده‌اند)
DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)

# --------------------------------------------------
# توابع کمکی (Async to Sync Helpers)
# --------------------------------------------------

# فرض می‌شود این توابع به صورت همزمان (Sync) در جایی در فایل تعریف شده‌اند
def normalize_digits(text):
    # فرض می‌شود منطق normalize_digits در اینجا وجود دارد
    return text.strip()

def _run_geocode_sync(city_name):
    # این تابع باید منطق geopy را به صورت همزمان (Sync) اجرا کند
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="telegram_bot")
    return geolocator.geocode(city_name, timeout=10)

def _run_horoscope_sync(data):
    # این تابع باید منطق اصلی شما را به صورت همزمان (Sync) اجرا کند
    return "متن پیش‌فرض طالع‌بینی", None # خروجی نمونه

def get_healing_text():
    # این تابع باید متن شفابخشی را به صورت همزمان (Sync) برگرداند
    return "متن شفابخشی پیش‌فرض" 

# --------------------------------------------------
# توابع هندلر (Async Handlers)
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فرض می‌شود تابع اصلی start در اینجا وجود دارد
    if update.message:
        await update.message.reply_text("خوش آمدید! از منوی زیر انتخاب کنید.")
    else:
         # اگر از callback_query فراخوانی شده
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
        # NOTE: از آنجا که این هندلر async است و geocode همزمان، از asyncio.to_thread استفاده می‌کنیم
        location = await asyncio.to_thread(_run_geocode_sync, city_name) 

        if location:
            context.user_data['lat'] = location.latitude
            context.user_data['lon'] = location.longitude

            data = context.user_data
            
            # NOTE: اجرای تابع همزمان _run_horoscope_sync در یک Thread
            text, img_path = await asyncio.to_thread(_run_horoscope_sync, data)
            
            if img_path and os.path.exists(img_path):
                 # فرض می‌کنیم os.path.exists و open در یک محیط async مشکلی ایجاد نمی‌کند
                 # اگر مشکل داشت، باید این قسمت را نیز در asyncio.to_thread اجرا کنید
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
    text = get_healing_text() # تابع همزمان
    await query.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context) 
    return ConversationHandler.END


# ----------------- Dispatcher / Application -----------------

# NOTE: خطای rate_limit_delay رفع شد
app_bot = ApplicationBuilder().token(TOKEN).rate_limiter(1).build()

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

# NOTE: تابع تنظیم Webhook برای اجرای همزمان توسط Flask Hook
def set_webhook_sync():
    """تنظیم وب‌هوک به صورت همزمان با استفاده از asyncio.run"""
    webhook_url_full = WEBHOOK_URL + "/webhook" 
    try:
        # برای اجرای یک تابع async در محیط sync
        asyncio.run(app_bot.bot.set_webhook(webhook_url_full))
        logging.info(f"Webhook set to {webhook_url_full}")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")

@app.before_request
def setup_webhook_on_startup():
    """اجرای تنظیم وب‌هوک قبل از اولین درخواست Flask در Render"""
    # در محیط Render فقط یکبار تنظیم شود
    if os.environ.get("RENDER") and not getattr(setup_webhook_on_startup, 'executed', False):
        current_webhook = asyncio.run(app_bot.bot.get_webhook_info())
        target_url = WEBHOOK_URL + '/webhook'
        
        if current_webhook.url != target_url:
            set_webhook_sync()
        
        # جلوگیری از اجرای مجدد
        setup_webhook_on_startup.executed = True
        
    
# NOTE: تابع webhook به حالت همزمان (Sync) تغییر داده شد تا با Gunicorn WSGI کار کند
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    پردازش به‌روزرسانی‌های دریافتی از تلگرام به صورت همزمان.
    """
    if request.method == "POST":
        # request.get_json همزمان است و نیازی به await ندارد
        json_data = request.get_json(force=True)
        
        try:
            # ایجاد شیء Update از داده‌های دریافتی
            update = Update.de_json(json_data, app_bot.bot) 
            
            # اجرای process_update به صورت همزمان (Sync)
            # این خط خطای 'object dict can't be used in await' را حل می‌کند
            app_bot.process_update(update)
            
            return "ok", 200 
            
        except Exception as e:
            logging.error(f"Error processing webhook update: {e}")
            return "error", 500
    
    # برای سایر متدها یا Health Check توسط Render
    return "Method not allowed", 405


# ----------------- اجرای برنامه (فقط برای تست لوکال) -----------------
if __name__ == "__main__":
    if not TOKEN or not WEBHOOK_URL:
        logging.error("Error: TELEGRAM_TOKEN or WEBHOOK_URL not set.")
    else:
        # تنظیم وب‌هوک به صورت لوکال
        setup_webhook_on_startup() 

        logging.info(f"Flask App running on port {PORT}")
        app.run(host="0.0.0.0", port=PORT)
