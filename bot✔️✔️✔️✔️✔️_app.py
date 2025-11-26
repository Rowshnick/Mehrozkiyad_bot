import os
import logging
import asyncio  # اضافه شده برای مدیریت Async
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# ماژول‌های جانبی شما (مطمئن شوید این فایل‌ها وجود دارند)
from utils.horoscope_service import get_horoscope_with_image
from utils.healing_service import get_healing_text
from utils.date_conv import gregorian_to_jalali, jalali_to_gregorian

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
app = Flask(__name__)

# --- توابع ربات ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    message_text = "سلام! من بات حرفه‌ای هستم. یکی از گزینه‌ها را انتخاب کنید:"
    
    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text(message_text, reply_markup=reply_markup)

# --- هندلرهای هوروسکوپ ---
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
        await update.message.reply_text("لطفا عدد صحیح وارد کنید. روز:")
        return DAY

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['month'] = int(update.message.text)
        await update.message.reply_text("سال تولد خود را وارد کنید (مثلاً: 1990)")
        return YEAR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح وارد کنید. ماه:")
        return MONTH

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['year'] = int(update.message.text)
        await update.message.reply_text("ساعت تولد (اختیاری، اگر ندارید 12 وارد کنید)")
        return HOUR
    except ValueError:
        await update.message.reply_text("لطفا عدد صحیح وارد کنید. سال:")
        return YEAR

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
    await update.message.reply_text("در حال پردازش... لطفاً صبر کنید.")
    
    try:
        # نکته: geolocator در ترد اصلی ممکن است بلاک شود، اما فعلاً برای سادگی نگه داشته شده
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
            if img_path and os.path.exists(img_path):
                 await update.message.reply_photo(photo=open(img_path, 'rb'), caption=text)
            else:
                 await update.message.reply_text(text)
            return ConversationHandler.END
        else:
            await update.message.reply_text("شهر پیدا نشد. مجدد تلاش کنید.")
            return CITY
    except Exception as e:
        logging.error(f"Error in get_city: {e}")
        await update.message.reply_text("خطا در دریافت موقعیت. لطفاً دوباره تلاش کنید.")
        return CITY

async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_healing_text()
    await query.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# --- ساخت ربات ---
# نکته مهم: initialize() باید بعداً فراخوانی شود
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

app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(horoscope_conv)
app_bot.add_handler(CallbackQueryHandler(healing_start, pattern='^healing$'))
app_bot.add_handler(CallbackQueryHandler(start, pattern='^intro$|^about$|^shop$|^register$'))


# --- تابع کمکی برای اجرای کدهای Async در Flask ---
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
             loop = asyncio.new_event_loop()
             asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# --- Flask Webhook Route ---
@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    # 1. جلوگیری از خطای 405 هنگام تست در مرورگر
    if request.method == "GET":
        return "Bot is running! Send POST request for updates.", 200

    # 2. پردازش درخواست POST تلگرام
    if request.method == "POST":
        try:
            # دریافت JSON
            update_json = request.get_json(force=True)
            # تبدیل به آبجکت Update
            update = Update.de_json(update_json, app_bot.bot)
            
            # اجرای پردازش به صورت Async
            # نکته حیاتی: process_update یک coroutine است و باید در loop اجرا شود
            async def process():
                await app_bot.initialize() # اطمینان از لود شدن بات
                await app_bot.process_update(update)
                await app_bot.shutdown()

            run_async(process())
            
            return "ok", 200
        except Exception as e:
            logging.error(f"Error in webhook: {e}")
            return "error", 500
            
    return "Method not allowed", 405


# --- تابع تنظیم وب‌هوک هنگام استارت ---
async def set_webhook_async():
    webhook_url_full = f"{WEBHOOK_URL}"
    logging.info(f"Setting webhook to: {webhook_url_full}")
    await app_bot.bot.set_webhook(webhook_url_full)

# --- اجرای برنامه ---
if __name__ == "__main__":
    if not TOKEN or not WEBHOOK_URL:
        print("Error: TELEGRAM_TOKEN or WEBHOOK_URL not set.")
    else:
        # اجرای تنظیم وب‌هوک (فقط یک بار هنگام شروع)
        try:
            run_async(set_webhook_async())
        except Exception as e:
            logging.error(f"Failed to set webhook: {e}")

        # اجرای سرور Flask
        app.run(host="0.0.0.0", port=PORT)
