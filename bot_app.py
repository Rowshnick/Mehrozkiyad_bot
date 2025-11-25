import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

from utils.horoscope_service import get_horoscope_with_image

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")  # برای پرداخت آنلاین

# مراحل دریافت داده‌ها
DAY, MONTH, YEAR, HOUR, MINUTE, LAT, LON = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("هوروسکوپ", callback_data='horoscope')],
        [InlineKeyboardButton("هیولینگ", callback_data='healing')],
        [InlineKeyboardButton("تبدیل تاریخ", callback_data='date_conv')],
        [InlineKeyboardButton("درباره ما", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام! من بات هوروسکوپ حرفه‌ای هستم.", reply_markup=reply_markup)

# --- دریافت تاریخ و مکان ---
async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text("ساعت تولد (اختیاری، برای دقت بهتر، اگر ندارید 12 وارد کنید)")
    return HOUR

async def get_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['hour'] = int(text) if text.isdigit() else 12
    await update.message.reply_text("دقیقه تولد (اختیاری، اگر ندارید 0 وارد کنید)")
    return MINUTE

async def get_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['minute'] = int(text) if text.isdigit() else 0
    await update.message.reply_text("عرض جغرافیایی محل تولد (مثلاً تهران: 35.6892)")
    return LAT

async def get_lat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lat'] = float(update.message.text)
    await update.message.reply_text("طول جغرافیایی محل تولد (مثلاً تهران: 51.3890)")
    return LON

async def get_lon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lon'] = float(update.message.text)
    data = context.user_data
    text, img_path = get_horoscope_with_image(
        year=data['year'], month=data['month'], day=data['day'],
        hour=data['hour'], minute=data['minute'],
        lat=data['lat'], lon=data['lon']
    )
    await update.message.reply_photo(photo=open(img_path, 'rb'), caption=text)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(horoscope_start, pattern='horoscope')],
        states={
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
            MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_month)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
            HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hour)],
            MINUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_minute)],
            LAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lat)],
            LON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lon)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

