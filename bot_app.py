import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from persiantools.jdatetime import JalaliDate

from utils.horoscope_service import get_horoscope_with_image
from utils.healing_service import get_healing_text  # فرض کنیم این سرویس موجود است

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")

# مراحل دریافت داده‌ها
DAY, MONTH, YEAR, HOUR, MINUTE, CITY = range(6)
DATE_CONV_DAY, DATE_CONV_MONTH, DATE_CONV_YEAR = range(100, 103)  # برای تبدیل تاریخ

geolocator = Nominatim(user_agent="horoscope_bot")


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


# --- هیولینگ ---
async def healing_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = get_healing_text()
    await update.callback_query.message.reply_text(text)
    return ConversationHandler.END


# --- تبدیل تاریخ ---
async def date_conv_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("روز را وارد کنید (مثلاً: 17)")
    return DATE_CONV_DAY


async def date_conv_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day_conv'] = int(update.message.text)
    await update.message.reply_text("ماه را وارد کنید (مثلاً: 5)")
    return DATE_CONV_MONTH


async def date_conv_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month_conv'] = int(update.message.text)
    await update.message.reply_text("سال را وارد کنید (مثلاً: 1990)")
    return DATE_CONV_YEAR


async def date_conv_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    y = context.user_data['year_conv'] = int(update.message.text)
    m = context.user_data['month_conv']
    d = context.user_data['day_conv']
    try:
        jalali = JalaliDate(y, m, d).to_jalali()
        text = f"تاریخ شمسی: {jalali.year}/{jalali.month}/{jalali.day}\nتاریخ میلادی: {y}/{m}/{d}"
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text("خطا در تبدیل تاریخ. لطفاً دوباره امتحان کنید.")
        return DATE_CONV_DAY
    return ConversationHandler.END


# --- درباره ما ---
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "این بات توسط تیم Roshina Nikzad توسعه داده شده است و خدمات هوروسکوپ و هیولینگ ارائه می‌دهد."
    await update.callback_query.message.reply_text(text)


# --- لغو ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # ConversationHandler برای هوروسکوپ
    horoscope_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(horoscope_start, pattern='horoscope')],
        states={
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
            MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_month)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
            HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hour)],
            MINUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_minute)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # ConversationHandler برای تبدیل تاریخ
    date_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(date_conv_start, pattern='date_conv')],
        states={
            DATE_CONV_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_conv_day)],
            DATE_CONV_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_conv_month)],
            DATE_CONV_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_conv_year)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(horoscope_handler)
    app.add_handler(date_conv_handler)
    app.add_handler(CallbackQueryHandler(healing_start, pattern='healing'))
    app.add_handler(CallbackQueryHandler(about, pattern='about'))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()



