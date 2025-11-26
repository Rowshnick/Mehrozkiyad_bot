# ----------------------------------------------------------------------
# bot_app.py - ربات تلگرام مبتنی بر FastAPI و python-telegram-bot
# ----------------------------------------------------------------------

import os
import logging
import json
import asyncio
from datetime import datetime, time
import pytz
# وارد کردن کتابخانه‌های مورد نیاز شما که در لاگ‌ها دیده شدند:
import pyswisseph as swe
from persiantools.jdatetime import JalaliDate
from PIL import Image, ImageDraw, ImageFont # برای مثال، اگر برای چارت‌سازی استفاده می‌کنید
from typing import Dict, Any

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)

# 1. تنظیمات اولیه و لاگینگ
# -------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# خواندن متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN") 
WEBHOOK_URL = os.getenv("WEBHOOK_URL") 
PORT = int(os.getenv("PORT", 8000))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set. Application cannot run.")
    raise ValueError("BOT_TOKEN environment variable not set.")

# تنظیم منطقه زمانی (UTC برای سرورهای Render معمول است)
TZ = pytz.timezone('UTC')

# 2. تعریف Stateها و توابع سفارشی (منطق اصلی شما)
# -------------------------------------------------

# Stateها برای ConversationHandler
SELECTING_SIGN = 0 
# ... (هر State دیگری که دارید) ...

# ⚠️ **مهم:** منطق اصلی شما که نیاز به pyswisseph یا persiantools دارد

def is_valid_persian_month(text: str) -> bool:
    """بررسی می‌کند که آیا متن وارد شده یک ماه شمسی معتبر است."""
    persian_months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 
                      'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    return text in persian_months

def get_horoscope_info(sign: str) -> str:
    """مثال Placeholder برای دریافت اطلاعات طالع‌بینی."""
    # ⚠️ **مهم:** منطق واقعی شما برای پردازش و دریافت اطلاعات اینجا قرار می‌گیرد
    
    # مثال داده‌های نجومی که از نتایج جستجو استخراج شده است:
    data: Dict[str, Dict[str, str]] = {
        'فروردین': {'نماد': 'قوچ', 'عنصر': 'آتش', 'روز خوش‌یمن': 'سه‌شنبه'},
        'مرداد': {'نماد': 'شیر', 'عنصر': 'آتش', 'روز خوش‌یمن': 'یکشنبه'},
        'شهریور': {'نماد': 'فرشته/خوشه گندم', 'عنصر': 'خاک', 'روز خوش‌یمن': 'چهارشنبه'},
        'مهر': {'نماد': 'ترازو', 'عنصر': 'هوا', 'روز خوش‌یمن': 'جمعه'},
        'آبان': {'نماد': 'عقرب', 'عنصر': 'آب', 'روز خوش‌یمن': 'سه‌شنبه'},
        # ... (سایر ماه‌ها را اضافه کنید)
    }

    info = data.get(sign, {})
    if info:
        return (
            f"🔮 **طالع‌بینی ماه {sign}**:\n"
            f"- نماد: {info.get('نماد')}\n"
            f"- عنصر: {info.get('عنصر')}\n"
            f"- روز خوش‌یمن: {info.get('روز خوش‌یمن')}\n"
            f"_(این اطلاعات از داده‌های نجومی استاندارد استخراج شده است.)_"
        )
    return "متأسفانه اطلاعاتی برای این ماه پیدا نشد."

# 3. توابع هندلر ناهمگام (Async Handlers)
# --------------------------------------
# همه توابع باید async def باشند تا با PTB کار کنند

async def start(update: Update, context: CallbackContext.DEFAULT_TYPE):
    """هندلر فرمان /start"""
    await update.message.reply_text(
        "✨ به ربات نجومی خوش آمدید! برای شروع، از /horoscope استفاده کنید."
    )

async def horoscope_start(update: Update, context: CallbackContext.DEFAULT_TYPE):
    """نقطه ورود ConversationHandler: درخواست ماه تولد"""
    await update.message.reply_text(
        "لطفاً **نام ماه تولد شمسی** خود (مانند فروردین یا مرداد) را وارد کنید:"
    )
    return SELECTING_SIGN

async def horoscope_sign(update: Update, context: CallbackContext.DEFAULT_TYPE):
    """پردازش ماه تولد و ارائه طالع‌بینی"""
    user_input = update.message.text
    if user_input and is_valid_persian_month(user_input):
        
        # ⚠️ **مهم:** اگر از pyswisseph برای محاسبات لحظه‌ای استفاده می‌کنید،
        # کد شما باید اینجا فراخوانی شود و منتظر آن بمانید (اگر آن هم Async است).
        
        info = get_horoscope_info(user_input)
        await update.message.reply_text(info, parse_mode='Markdown')
        # پایان مکالمه
        return ConversationHandler.END 
    else:
        await update.message.reply_text(
            "ورودی نامعتبر است. لطفاً یک نام ماه شمسی صحیح وارد کنید (مثلاً: اردیبهشت)."
        )
        # ماندن در همین مرحله
        return SELECTING_SIGN 

async def cancel(update: Update, context: CallbackContext.DEFAULT_TYPE):
    """هندلر برای لغو مکالمه"""
    await update.message.reply_text("عملیات لغو شد. می‌توانید دوباره شروع کنید.")
    return ConversationHandler.END


# 4. ساختن Application و اضافه کردن هندلرها
# ------------------------------------------

application = Application.builder().token(BOT_TOKEN).build()

# تعریف ConversationHandler
horoscope_conv = ConversationHandler(
    entry_points=[CommandHandler("horoscope", horoscope_start)],
    states={
        SELECTING_SIGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_sign)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    # هشدار PTBUserWarning مربوط به ConversationHandler معمولاً به دلیل 
    # استفاده نادرست از CallbackQueryHandler در states است. 
    # اگر CallbackQueryHandler دارید، مطمئن شوید که per_message=True است یا تنظیمات آن درست است.
)

# اضافه کردن هندلرهای اصلی
application.add_handler(CommandHandler("start", start))
application.add_handler(horoscope_conv)
# ... (تمام application.add_handler های دیگر را اینجا اضافه کنید) ...


# 5. تعریف برنامه FastAPI و Webhook Handler
# ------------------------------------------

app = FastAPI()

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    هندلر وب‌هوک ناهمگام. **این بخش خطای RuntimeWarning را رفع می‌کند.**
    """
    try:
        # 1. دریافت داده‌های JSON از درخواست
        update_json = await request.json()
        
        # 2. تبدیل JSON به شیء Update PTB
        update = Update.de_json(update_json, application.bot)

        # 3. فراخوانی ناهمگام process_update و انتظار برای آن
        # 🌟 این خط کلیدی است: استفاده از 'await'
        await application.process_update(update) 
        
        # پاسخ 200 OK به تلگرام
        return {"message": "OK"}
        
    except json.JSONDecodeError:
        logger.warning("Received non-JSON request on webhook path.")
        return {"message": "Invalid JSON"}, 200
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        # حتی در صورت خطای داخلی، 200 OK برگردانید تا از تلاش مجدد تلگرام جلوگیری شود
        return {"message": "Internal Error"}, 200


@app.get("/")
async def health_check():
    """بررسی سلامت سرویس برای Render."""
    return {"status": "ok", "message": "Bot is running and listening for webhooks."}


# 6. تنظیم Webhook هنگام راه‌اندازی (Startup)
# ---------------------------------------------
@app.on_event("startup")
async def set_webhook():
    """
    تنظیم Webhook URL در سرورهای تلگرام.
    """
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not set. Webhook will not be set automatically.")
        return

    full_webhook_url = WEBHOOK_URL + "/webhook"

    try:
        logger.info(f"Setting webhook to: {full_webhook_url}")
        
        # set_webhook ناهمگام است
        await application.bot.set_webhook(url=full_webhook_url)
        
        # تأیید تنظیم
        info = await application.bot.get_webhook_info()
        logger.info(f"Webhook set successfully. Pending updates: {info.pending_update_count}")
    
    except Exception as e:
        logger.error(f"Could not set webhook: {e}", exc_info=True)

