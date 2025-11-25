# bot_app.py - نسخه اصلاح شده برای محیط WebHook

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

# فرض می‌شود این ماژول‌ها در دایرکتوری utils موجود و قابل دسترس هستند
from utils.horoscope_service import get_horoscope_with_image
from utils.healing_service import get_healing_text
# from utils.date_conv import gregorian_to_jalali, jalali_to_gregorian # فعلاً در کد اصلی استفاده نشده
from utils.hafez_service import get_random_hafez_verse 

# --- تنظیمات اولیه و متغیرهای محیطی ---
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
# این آدرس باید آدرس عمومی (Public URL) سرور شما باشد، مثال: https://mehrozkiyad-bot.onrender.com
WEBHOOK_URL = os.getenv("WEBHOOK_URL") 
PORT = int(os.environ.get("PORT", 5000)) # استفاده از پورت 5000 یا متغیر محیطی PORT

# مراحل دریافت داده‌ها
DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)
DATE_CONV_DAY, DATE_CONV_MONTH, DATE_CONV_YEAR = range(100, 103)

geolocator = Nominatim(user_agent="horoscope_bot")

# --- Flask App ---
app = Flask(__name__)

# --- توابع ربات ---

# --- استارت و منو (اصلاح شده) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    نمایش منوی اصلی. پیام قبلی را در صورت فراخوانی از طریق دکمه، ویرایش می‌کند.
    """
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
    message_text = "سلام! من بات حرفه‌ای هستم. یکی از گزینه‌ها را انتخاب کنید:"
    
    if update.message:
        # اگر از طریق دستور /start فراخوانی شده
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif update.callback_query:
        # اگر از طریق دکمه‌ها (مثلاً از کنسل شدن یک فرایند) فراخوانی شده
        query = update.callback_query
        await query.answer()
        # پیام قبلی را ویرایش می‌کنیم تا از ارسال پیام‌های اضافی جلوگیری شود
        await query.message.edit_text(message_text, reply_markup=reply_markup)


# --- هوروسکوپ ---
# (توابع horoscope_start تا get_city بدون تغییر مهم باقی می‌مانند)
async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("لطفاً روز تولد خود را وارد کنید (مثلاً: 17)")
    return DAY

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['day'] = int(update.message.text)
        await update.message.reply_text("ماه تولد خود را وارد کنید (مثلاً: 5)")
        return MONTH
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح وارد کنید. روز تولد خود را وارد کنید:")
        return DAY


async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['month'] = int(update.message.text)
        await update.message.reply_text("سال تولد خود را وارد کنید (مثلاً: 1990)")
        return YEAR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح وارد کنید. ماه تولد خود را وارد کنید:")
        return MONTH

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['year'] = int(update.message.text)
        await update.message.reply_text("ساعت تولد (اختیاری، اگر ندارید 12 وارد کنید)")
        return HOUR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح وارد کنید. سال تولد خود را وارد کنید:")
        return YEAR

async def get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # اضافه شدن مدیریت خطا برای ورودی غیرعددی
    try:
        context.user_data['hour'] = int(text) if text.isdigit() else 12
        await update.message.reply_text("دقیقه تولد (اختیاری، اگر ندارید 0 وارد کنید)")
        return MINUTE
    except Exception:
        context.user_data['hour'] = 12
        await update.message.reply_text("فرمت ساعت اشتباه بود، 12 در نظر گرفته شد. دقیقه تولد را وارد کنید (اختیاری، اگر ندارید 0 وارد کنید):")
        return MINUTE


async def get_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # اضافه شدن مدیریت خطا برای ورودی غیرعددی
    try:
        context.user_data['minute'] = int(text) if text.isdigit() else 0
    except Exception:
        context.user_data['minute'] = 0
    
    await update.message.reply_text("لطفاً نام شهر یا مکان تولد خود را وارد کنید (مثلاً: تهران)")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_name = update.message.text.strip()
    await update.message.reply_text("در حال پردازش درخواست شما... لطفاً صبر کنید.")
    
    try:
        location = geolocator.geocode(city_name, timeout=20) # افزایش تایم‌آوت
        if location:
            context.user_data['lat'] = location.latitude
            context.user_data['lon'] = location.longitude

            data = context.user_data
            text, img_path = get_horoscope_with_image(
                year=data['year'], month=data['month'], day=data['day'],
                hour=data['hour'], minute=data['minute'],
                lat=data['lat'], lon=data['lon']
            )
            # ارسال عکس و کپشن
            await update.message.reply_photo(photo=open(img_path, 'rb'), caption=text)
            return ConversationHandler.END
        else:
            await update.message.reply_text("شهر وارد شده پیدا نشد. لطفاً نام شهر را دقیق وارد کنید.")
            return CITY
    except GeocoderTimedOut:
        logging.error("Geocoder Timed Out")
        await update.message.reply_text("خطا در اتصال به سرویس موقعیت‌یابی، دوباره تلاش کنید.")
        return CITY
    except Exception as e:
        logging.error(f"Error in get_city: {e}")
        await update.message.reply_text("خطایی رخ داد. لطفاً مطمئن شوید اطلاعات ورودی معتبر هستند.")
        return CITY


# --- درمان (هیولینگ) ---
async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # از context.bot.send_message برای پاسخ در CallbackQuery استفاده کنید
    query = update.callback_query
    await query.answer()
    text = get_healing_text()
    await query.message.reply_text(text)
    # نیازی به بازگشت ConversationHandler.END نیست مگر اینکه در یک ConversationHandler باشید.

# --- فال حافظ ---
async def hafez_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    verse = get_random_hafez_verse()
    await query.message.reply_text(f"فال حافظ شما:\n\n{verse}")

# --- لغو ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فراخوانی start برای بازگشت به منوی اصلی
    await start(update, context)
    return ConversationHandler.END

# --- Dispatcher / Application ---
app_bot = ApplicationBuilder().token(TOKEN).build()

# --- ConversationHandlers ---
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
app_bot.add_handler(CallbackQueryHandler(hafez_start, pattern='^hafez$'))
# در صورت نیاز به بازگشت به منو از دکمه‌ها
app_bot.add_handler(CallbackQueryHandler(start, pattern='^intro$|^about$|^shop$|^register$'))


# --- Flask route for webhook (اصلاح شده) ---
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    پردازش به‌روزرسانی‌های دریافتی از تلگرام و ارسال مستقیم آن به Application
    """
    if request.method == "POST":
        try:
            # تلگرام یک JSON با آپدیت می‌فرستد.
            # استفاده از Update.de_json برای تبدیل داده‌های JSON به آبجکت Update
            update = Update.de_json(request.get_json(force=True), app_bot.bot)
            
            # استفاده از process_update برای پردازش مستقیم آپدیت (مخصوص وب‌هوک)
            app_bot.process_update(update)
            
        except Exception as e:
            logging.error(f"Error processing update: {e}")
            # مهم است که حتی در صورت خطا، 'ok' برگردانده شود تا تلگرام مجدداً تلاش نکند
        return "ok"
    return "Method not allowed", 405


# --- اجرای برنامه ---
if __name__ == "__main__":
    if TOKEN is None or WEBHOOK_URL is None:
        logging.error("TELEGRAM_TOKEN or WEBHOOK_URL environment variables not set.")
    
    # 1. تنظیم وب‌هوک
    try:
        # حذف هر وب‌هوک قدیمی (اختیاری، اما توصیه می‌شود)
        app_bot.bot.delete_webhook() 
        webhook_url_full = f"{WEBHOOK_URL}/webhook"
        logging.info(f"Setting webhook to: {webhook_url_full}")
        app_bot.bot.set_webhook(webhook_url_full)
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")

    # 2. اجرای سرور Flask
    logging.info(f"Flask App running on port {PORT}")
    # اگر از Gunicorn یا مشابه آن استفاده می‌کنید، این خط در Production اجرا نخواهد شد
    # اما برای اجرای لوکال یا دیباگ مناسب است.
    app.run(host="0.0.0.0", port=PORT)

