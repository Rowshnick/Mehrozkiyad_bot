import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
# برای اجرای بهتر در محیط Flask، از AsyncHTTPRequester استفاده می‌کنیم
from telegram.request import HTTPXRequest 
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# ماژول‌های جانبی شما
from utils.horoscope_service import get_horoscope_with_image
from utils.healing_service import get_healing_text
from utils.date_conv import gregorian_to_jalali, jalali_to_gregorian

# ----------------- تنظیمات -----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

# مراحل دریافت داده‌ها
DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)
geolocator = Nominatim(user_agent="horoscope_bot")

# --- Flask App ---
# در حالت واقعی، Flask برای Webhook باید به صورت async اجرا شود (مثلاً با Uvicorn/Gunicorn)
app = Flask(__name__)

# ----------------- توابع کمکی -----------------

def normalize_digits(text: str) -> str:
    """تبدیل ارقام فارسی/عربی به ارقام استاندارد (ASCII)"""
    if not isinstance(text, str):
        return str(text)
        
    mapping = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    text = text.strip() 
    return ''.join(mapping.get(c, c) for c in text)

def _run_geocode_sync(city_name):
    """تابع همگام برای فراخوانی geolocator (I/O مسدودکننده)"""
    # توجه: این تابع در یک Threadpool اجرا خواهد شد.
    return geolocator.geocode(city_name, timeout=20)

def _run_horoscope_sync(data):
    """تابع همگام برای تولید هوروسکوپ و تصویر (محاسبات و I/O)"""
    # توجه: این تابع در یک Threadpool اجرا خواهد شد.
    return get_horoscope_with_image(
        year=data['year'], month=data['month'], day=data['day'],
        hour=data['hour'], minute=data['minute'],
        lat=data['lat'], lon=data['lon']
    )

# ----------------- توابع ربات (Async) -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی به صورت Inline Keyboard."""
    keyboard = [
        [InlineKeyboardButton("هوروسکوپ (ستاره شناسی)", callback_data='horoscope')],
        [InlineKeyboardButton("درمان (هیولینگ)", callback_data='healing')],
        [InlineKeyboardButton("چارت تولد (ستاره شناسی)", callback_data='chart')],
        [InlineKeyboardButton("فروشگاه محصولات درمانی", callback_data='shop')],
        [InlineKeyboardButton("عضویت در ربات", callback_data='register')],
        [InlineKeyboardButton("درباره ما", callback_data='about')],
        [InlineKeyboardButton("معرفی ربات", callback_data='intro')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = "سلام! من بات حرفه‌ای هستم. یکی از گزینه‌ها را انتخاب کنید: 🔮"
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text(message_text, reply_markup=reply_markup)
        
    elif update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
        
    else:
        await context.bot.send_message(update.effective_chat.id, message_text, reply_markup=reply_markup)


# --- هوروسکوپ (بدون تغییر در منطق مکالمه) ---

async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("لطفاً روز تولد خود را وارد کنید (مثلاً: 17) 📅")
    return DAY

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        day_text = normalize_digits(update.message.text)
        context.user_data['day'] = int(day_text)
        await update.message.reply_text("ماه تولد خود را وارد کنید (مثلاً: 5) 🌕")
        return MONTH
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **روز** وارد کنید:")
        return DAY

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        month_text = normalize_digits(update.message.text)
        context.user_data['month'] = int(month_text)
        await update.message.reply_text("سال تولد خود را وارد کنید (مثلاً: 1990) 🗓️")
        return YEAR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **ماه** وارد کنید:")
        return MONTH

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        year_text = normalize_digits(update.message.text)
        context.user_data['year'] = int(year_text)
        await update.message.reply_text("ساعت تولد (اختیاری، اگر ندارید 12 وارد کنید) ⏰")
        return HOUR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح برای **سال** وارد کنید:")
        return YEAR

async def get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = normalize_digits(update.message.text)
        context.user_data['hour'] = int(text) if text.isdigit() else 12 
        await update.message.reply_text("دقیقه تولد (اختیاری، اگر ندارید 0 وارد کنید) ⏱️")
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
    """
    دریافت نام شهر و اجرای فرایندهای سنگین (با asyncio.to_thread برای رفع مشکل blocking)
    """
    city_name = update.message.text.strip()
    await update.message.reply_text("در حال پردازش درخواست شما... لطفاً صبر کنید. ⏳")
    
    try:
        # **گام ۱: Geocoding (اجرای Blocking I/O در یک ترد مجزا)**
        location = await asyncio.to_thread(_run_geocode_sync, city_name) 

        if location:
            context.user_data['lat'] = location.latitude
            context.user_data['lon'] = location.longitude

            data = context.user_data
            
            # **گام ۲: تولید هوروسکوپ (اجرای Blocking محاسبات در یک ترد مجزا)**
            text, img_path = await asyncio.to_thread(_run_horoscope_sync, data)
            
            # گام ۳: پاسخ به کاربر
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


# --- درمان (هیولینگ) ---
async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_healing_text()
    await query.message.reply_text(text)

# --- لغو ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context) 
    return ConversationHandler.END

# ----------------- Dispatcher / Application -----------------

# استفاده از HTTPXRequest برای پایداری بیشتر در محیط‌های ناهمزمان
app_bot = ApplicationBuilder().token(TOKEN).rate_limit_delay(1).build()

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


# ----------------- توابع Flask و Webhook (اصلاح شده) -----------------

# **حذف تابع run_async که باعث خطای Loop می‌شد**



async def set_webhook_async(application):
    """تنظیم وب‌هوک به صورت ناهمزمان"""
    webhook_url_full = WEBHOOK_URL + "/webhook" # اضافه کردن مسیر webhook به URL اصلی
    logging.info(f"Setting webhook to: {webhook_url_full}")
    await application.bot.set_webhook(webhook_url_full)

# **اصلاح تابع webhook برای استفاده از loop موجود و مدیریت صحیح ناهمزمانی**
@app.route("/webhook", methods=["POST"])
async def webhook():
    """
    پردازش به‌روزرسانی‌های دریافتی از تلگرام به صورت ناهمزمان.
    **نکته: برای اجرای این تابع به صورت async باید از یک سرور ASGI (مانند Uvicorn) استفاده کنید.**
    اگر از 'python bot_app.py' در Render استفاده می‌کنید، ممکن است نیاز به تغییر دستور اجرا در Render داشته باشید.
    """
    if request.method == "POST":
        try:
            update = Update.de_json(await request.get_json(force=True), app_bot.bot)
            
            # اجرای process_update
            await app_bot.process_update(update)
            
            # پاسخ فوری 200 OK
            return "ok", 200 
            
        except Exception as e:
            logging.error(f"Error processing webhook update: {e}")
            return "error", 500
    
    return "Method not allowed", 405


# ----------------- اجرای برنامه -----------------
if __name__ == "__main__":
    if not TOKEN or not WEBHOOK_URL:
        print("Error: TELEGRAM_TOKEN or WEBHOOK_URL not set.")
    else:
        # **ابتدا وب‌هوک را تنظیم و سپس سرور را اجرا می‌کنیم.**
        try:
            # ایجاد یک Loop جدید برای تنظیم وب‌هوک (چون در main thread هنوز Loop فعال نیست)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(set_webhook_async(app_bot))
        except Exception as e:
            logging.error(f"Failed to set webhook: {e}")

        logging.info(f"Flask App running on port {PORT}")
        
        # **توجه: برای اجرای تابع async webhook، نیاز به اجرای Flask با یک سرور ASGI دارید.**
        # **اگر دستور اجرای Render شما 'python bot_app.py' است، آن را به موارد زیر تغییر دهید:**
        # gunicorn -w 4 -k uvicorn.workers.UvicornWorker bot_app:app
        
        app.run(host="0.0.0.0", port=PORT)


