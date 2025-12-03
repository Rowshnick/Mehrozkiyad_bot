import os
import datetime
import re
from fastapi import FastAPI, Request
from pydantic import BaseModel
from skyfield.api import load
from skyfield.framelib import ecliptic_frame
import json # اضافه شده برای استفاده احتمالی

# ======================================================================
# رفع خطای ModuleNotFoundError: ایمپورت‌های مطلق
# ======================================================================

# وارد کردن ماژول‌های داخلی
try:
    import utils
    import keyboards
    import astrology_core
    import data_lookup
    # ایمپورت کردن ماژول‌های سجیل (اگر این فایل‌ها موجود نیستند، لطفا حذف یا ایجاد شوند)
    import main_sajil 
    import sajil_part_one
    import sajil_part_two
except ImportError as e:
    # این خطا نشان می‌دهد که یکی از فایل‌های کمکی در فرآیند دیپلوی گنجانده نشده است.
    print(f"Error importing local modules: {e}. Ensure all .py files are in the deployment package.")
    # اگر utils.py یا keyboards.py گم شده باشند، اینجا خطا متوقف می شود.
    raise 

# ======================================================================
# 1. تنظیمات اولیه
# ======================================================================

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# بررسی وجود توکن
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set.")

# State نگهداری وضعیت مکالمه موقت (باید با یک دیتابیس واقعی جایگزین شود)
# {chat_id: {'state': 'EXPECTING_BIRTH_INFO', 'data': {}}}
CONVERSATION_STATE = {}

# ======================================================================
# 2. مدل‌های داده‌ای
# ======================================================================

class Update(BaseModel):
    update_id: int
    message: dict = None
    callback_query: dict = None

# ======================================================================
# 3. توابع اصلی هندلینگ (Routing)
# ======================================================================

async def handle_start_command(chat_id: int):
    """هندل کردن دستور /start یا /شروع"""
    welcome_text = (
        "✨ **به ربات تحلیل آسترولوژیک و نمادشناسی خوش آمدید!** ✨\n"
        "این ربات یک ابزار دقیق برای ارائه خدمات شخصی‌سازی‌شده بر پایه نجوم و نمادشناسی باستانی است.\n"
        "لطفاً از طریق کلیدهای زیر، سرویس مورد نظر خود را انتخاب کنید."
    )
    # فراخوانی توابع از ماژول‌های ایمپورت شده
    await utils.send_telegram_message(chat_id, welcome_text, "Markdown", keyboards.main_menu_keyboard())


async def handle_callback_query(chat_id: int, callback_data: str, message_id: int):
    """هندل کردن Callback Queryهای کلیدهای اینلاین"""
    
    # حذف وضعیت قبلی مکالمه در صورت تغییر مسیر
    CONVERSATION_STATE.pop(chat_id, None) 
    
    parts = callback_data.split('|')
    
    if len(parts) < 3:
        # ویرایش پیام قبلی برای رفع خطا
        await utils.send_telegram_message(chat_id, "❌ خطای داده. لطفاً از منوی اصلی استفاده کنید.", "Markdown", keyboards.main_menu_keyboard())
        return

    menu, submenu, action = parts[0], parts[1], parts[2]
    
    # 1. مسیردهی منوی اصلی و خدمات (بدون تغییر)
    if menu == 'MAIN':
        if submenu == 'SERVICES':
            await utils.send_telegram_message(chat_id, "بخش خدمات:", "Markdown", keyboards.services_menu_keyboard())
        elif submenu == 'SHOP':
            await utils.send_telegram_message(chat_id, "بخش فروشگاه و سفارشات:", "Markdown", keyboards.shop_menu_keyboard())
        elif submenu == 'SOCIALS':
            info_text = "🌐 **شبکه‌های اجتماعی و سایت**\nبرای مشاهده لینک‌ها، از کیبورد زیر استفاده کنید."
            await utils.send_telegram_message(chat_id, info_text, "Markdown", keyboards.socials_menu_keyboard())
        elif submenu == 'ABOUT':
            info_text = "🧑‍💻 **درباره ما**\n\nاین سیستم یک پروژه آکادمیک برای تحلیل نمادها است."
            await utils.send_telegram_message(chat_id, info_text, "Markdown", keyboards.main_menu_keyboard())
        elif submenu == 'WELCOME':
            await handle_start_command(chat_id)

    # 2. مسیردهی خدمات
    elif menu == 'SERVICES':
        # ... بخش ASTRO و GEM بدون تغییر
        if submenu == 'ASTRO':
            if action == '0':
                await utils.send_telegram_message(chat_id, "بخش آسترولوژی:", "Markdown", keyboards.astrology_menu_keyboard())
            elif action == 'CHART_INPUT':
                CONVERSATION_STATE[chat_id] = {'state': 'EXPECTING_BIRTH_INFO', 'step': 1, 'data': {}}
                
                input_text = (
                    "📝 **تولید چارت تولد (زایچه)**\n"
                    "لطفاً اطلاعات زیر را در یک خط و با فرمت مشخص وارد کنید:\n\n"
                    "**فرمت:** `نام، جنسیت، تاریخ تولد (YYYY/MM/DD)، ساعت تولد (HH:MM)، محل تولد (شهر)`\n"
                    "**مثال:** `علی، مذکر، ۱۳۷۰/۰۵/۲۲، ۱۷:۳۰، تهران`\n"
                )
                await utils.send_telegram_message(chat_id, input_text, "Markdown")
        
        elif submenu == 'GEM':
            if action == '0':
                await utils.send_telegram_message(chat_id, "بخش سنگ‌شناسی:", "Markdown", keyboards.gem_menu_keyboard())
            elif action == 'PERSONAL_INPUT':
                CONVERSATION_STATE[chat_id] = {'state': 'EXPECTING_GEM_INFO', 'step': 1, 'data': {}}
                input_text = (
                    "💎 **انتخاب سنگ مناسب شخصی**\n"
                    "لطفاً اطلاعات تولد و همچنین **نیت یا هدف** خود را وارد کنید (مثل: شغل، عشق، ثروت).\n\n"
                    "**فرمت:** `تاریخ (YYYY/MM/DD)، ساعت (HH:MM)، شهر، نیت`\n"
                    "**مثال:** `۱۳۷۰/۰۵/۲۲، ۱۷:۳۰، تهران، افزایش ثروت`"
                )
                await utils.send_telegram_message(chat_id, input_text, "Markdown")
                
        # --- بخش SIGIL (نمادشناسی) ---
        elif submenu == 'SIGIL':
            if action == '0':
                await utils.send_telegram_message(chat_id, "بخش نمادشناسی (سجیل):", "Markdown", keyboards.services_menu_keyboard())
            elif action == 'PERSONAL_INPUT':
                CONVERSATION_STATE[chat_id] = {'state': 'EXPECTING_SIGIL_INFO', 'step': 1, 'data': {}}
                input_text = (
                    "✨ **تولید نماد (سجیل) شخصی** ✨\n"
                    "برای تحلیل سجیل، لطفاً **سری اعداد و کلمات کلیدی** مرتبط با هدف خود را وارد کنید.\n\n"
                    "**فرمت:** `عدد ۱، عدد ۲، عدد ۳، ...`\n"
                    "**مثال:** `۱۰، ۵۵، ۱۲، ۳.۴، ۲۰`\n"
                    "*بعد از اتمام کار، ربات بر اساس این اعداد، تحلیل و نماد پیشنهادی را ارائه خواهد کرد.*"
                )
                await utils.send_telegram_message(chat_id, input_text, "Markdown")
        
        # ... پیاده‌سازی زیرمنوی HERB

    # 4. مسیردهی فروشگاه
    elif menu == 'SHOP':
        await utils.send_telegram_message(chat_id, "بخش فروشگاه در حال تکمیل است.", "Markdown", keyboards.shop_menu_keyboard())


# ======================================================================
# 4. هندلینگ پیام‌های متنی (Message Handler)
# ======================================================================

async def handle_text_message(chat_id: int, incoming_text: str):
    
    # 1. اگر کاربر در وضعیت خاصی است (مانند انتظار برای اطلاعات تولد یا سجیل)
    if chat_id in CONVERSATION_STATE:
        state_data = CONVERSATION_STATE[chat_id]
        
        # --- وضعیت انتظار برای اطلاعات تولد (ASTRO) ---
        if state_data['state'] == 'EXPECTING_BIRTH_INFO':
            # regex برای تطابق دقیق با فرمت: نام، جنسیت، تاریخ، ساعت، شهر
            match = re.match(r'(.+?)،\s*(.+?)،\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})،\s*(\d{1,2}:\d{1,2})،\s*(.+)', incoming_text)
            
            if match:
                name, gender, shamsi_date_str, time_str, city = match.groups()
                # ترکیب تاریخ و زمان برای تابع تبدیل
                shamsi_dt = f"{shamsi_date_str} {time_str}:00"
                
                print(f"DEBUG: Processing input for {name}, City: {city}") # چاپ برای دیباگ

                try:
                    # 1. تبدیل تاریخ و زمان
                    dt_utc = utils.parse_shamsi_to_utc_datetime(shamsi_dt)
                    
                    # 2. دریافت مختصات جغرافیایی (Async call)
                    coords = await utils.get_coordinates_from_city(city)
                
                except Exception as e:
                    # اگر خطایی در توابع utils رخ داد، اینجا گرفته می‌شود.
                    print(f"CRITICAL UTILS ERROR: {e}")
                    await utils.send_telegram_message(chat_id, f"❌ خطای داخلی هنگام تبدیل زمان یا مکان: {e}", "Markdown")
                    CONVERSATION_STATE.pop(chat_id)
                    return # جلوگیری از ادامه کار

                # بررسی اعتبار داده‌ها
                if dt_utc and coords:
                    lat, lon = coords
                    
                    try:
                        # 3. محاسبه چارت
                        natal_data = astrology_core.calculate_natal_chart(dt_utc, lat, lon)
                        
                        # 4. تولید خروجی
                        output = f"✨ **چارت تولد شخصی‌سازی شده برای {name} ({gender})**\n\n"
                        output += f"📅 **تاریخ شمسی:** {utils.convert_to_shamsi_date(dt_utc)}\n"
                        output += f"📍 **محل تولد:** {city} (عرض: {lat:.2f}، طول: {lon:.2f})\n\n"
                        
                        for planet, data in natal_data.items():
                             # اگر موقعیت محاسبه شده باشد (خاموش کردن Placeholderها)
                             if planet in ['Sun', 'Moon']:
                                # اگر داده['longitude'] عدد باشد:
                                try:
                                    long_str = f"{data['longitude']:.2f}°"
                                except TypeError:
                                     long_str = data['longitude'] # برای Placeholderها

                                output += f"☀️ **{planet} در:** {long_str} {data['sign_fa']}\n"
                             elif planet == 'Ascendant':
                                output += f"⬆️ **طالع (صعودی):** {data['sign_fa']}\n"
                        
                        output += "\n*توجه: محاسبه Houseها و Ascendant نیاز به کتابخانه نجومی تخصصی‌تر دارد.*"
                        
                        await utils.send_telegram_message(chat_id, output, "Markdown", keyboards.astrology_menu_keyboard())
                        CONVERSATION_STATE.pop(chat_id)
                        return
                    
                    except Exception as e:
                        # خطاهای محاسباتی در astrology_core
                        print(f"CRITICAL ASTROLOGY ERROR: {e}")
                        await utils.send_telegram_message(chat_id, f"❌ خطای حیاتی در محاسبه چارت نجومی: {e}", "Markdown")
                        CONVERSATION_STATE.pop(chat_id)
                        return
                        
                else:
                    # خطای عدم اعتبار (تاریخ/ساعت نامعتبر یا شهر پیدا نشد)
                    error_msg = "❌ **خطا در پردازش اطلاعات!**\n"
                    if not dt_utc:
                        error_msg += "خطا: فرمت تاریخ یا ساعت صحیح نیست (مثلاً ساعت ۲۵:۰۰ وارد شده).\n"
                    if not coords:
                        error_msg += f"خطا: نتوانستیم مختصات شهر '{city}' را پیدا کنیم. آیا نام شهر را درست وارد کرده‌اید؟\n"
                    await utils.send_telegram_message(chat_id, error_msg, "Markdown")
                    CONVERSATION_STATE.pop(chat_id) # وضعیت را پاک می کنیم
                    return
            
            # در صورتی که regex مطابقت نداشته باشد
            await utils.send_telegram_message(chat_id, "⚠️ **فرمت ورودی نادرست.** لطفاً مثال ارائه شده را دنبال کنید.", "Markdown")
            return
            
        # --- وضعیت انتظار برای اطلاعات سنگ‌شناسی (GEM) ---
        elif state_data['state'] == 'EXPECTING_GEM_INFO':
            match = re.match(r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})،\s*(\d{1,2}:\d{1,2})،\s*(.+?)،\s*(.+)', incoming_text)
            
            if match:
                # shamsi_date_str, time_str, city, intention = match.groups()
                # منطق سنگ‌شناسی از data_lookup.GEM_MAPPING استفاده خواهد کرد
                await utils.send_telegram_message(chat_id, f"✅ اطلاعات سنگ شناسی دریافت شد. (نیاز به پیاده‌سازی کامل منطق تطبیق)", "Markdown", keyboards.gem_menu_keyboard())
                CONVERSATION_STATE.pop(chat_id)
                return
            
            await utils.send_telegram_message(chat_id, "⚠️ **فرمت ورودی نادرست برای سنگ‌شناسی.** لطفاً مثال ارائه شده را دنبال کنید.", "Markdown")
            return
            
        # --- وضعیت انتظار برای اطلاعات سجیل (SIGIL) ---
        elif state_data['state'] == 'EXPECTING_SIGIL_INFO':
            # فراخوانی ماژول مدیریت جریان کار سجیل
            # اگر main_sajil وجود ندارد، این خط منجر به خطا می شود.
            await main_sajil.run_sajil_workflow(chat_id, incoming_text)
            
            # در صورت موفقیت/شکست، CONVERSATION_STATE در داخل run_sajil_workflow حذف می‌شود
            CONVERSATION_STATE.pop(chat_id, None)
            return
            
    # 2. هندل کردن دستورات اصلی
    if incoming_text == '/start' or incoming_text == '/شروع':
        CONVERSATION_STATE.pop(chat_id, None) 
        await handle_start_command(chat_id)
    elif incoming_text.startswith('/'):
        await utils.send_telegram_message(chat_id, "دستور نامعتبر. لطفاً از منوی اصلی استفاده کنید.", "Markdown", keyboards.main_menu_keyboard())
    else:
        await utils.send_telegram_message(chat_id, "پیام شما دریافت شد. لطفاً از طریق منوی اصلی با ربات تعامل کنید.", "Markdown", keyboards.main_menu_keyboard())

# ======================================================================
# 5. Endpoint اصلی Webhook
# ======================================================================

@app.post(f"/{TELEGRAM_TOKEN}")
async def telegram_webhook(update: Update):
    
    if update.message:
        chat_id = update.message['chat']['id']
        incoming_text = update.message.get('text', '')
        # این تابع async است، لذا باید با await فراخوانی شود.
        await handle_text_message(chat_id, incoming_text)
        
    elif update.callback_query:
        chat_id = update.callback_query['message']['chat']['id']
        message_id = update.callback_query['message']['message_id']
        callback_data = update.callback_query['data']
        
        # این تابع async است، لذا باید با await فراخوانی شود.
        await handle_callback_query(chat_id, callback_data, message_id)

    return {"ok": True}
