# ======================================================================
# ماژول اصلی ربات تلگرام با استفاده از FastAPI
# این برنامه درخواست‌های وب‌هوک تلگرام را دریافت و پردازش می‌کند.
# ======================================================================

from fastapi import FastAPI, Request, HTTPException, Body
from typing import Dict, Any, Optional
import os
import datetime # 👈 اصلاح: ایمپورت اضافه شد
import pytz     # 👈 اصلاح: ایمپورت اضافه شد

# ایمپورت‌های ماژول‌های داخلی (باید در کنار این فایل وجود داشته باشند)
import utils
import keyboards
import astrology_core
from persiantools.jdatetime import JalaliDateTime

# --- تنظیمات ضروری ---

# ⚠️ مهم: این متغیر باید در محیط دیپلوی (Environment Variables) تنظیم شود. 
# مقدار پیش‌فرض را حذف کردیم تا اگر تنظیم نشود، برنامه خطا دهد.
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# بررسی توکن در زمان اجرا
if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
    print("FATAL ERROR: BOT_TOKEN environment variable is not set correctly.")
    # می‌توانیم برنامه را در اینجا با خطا متوقف کنیم یا یک مقدار پیش‌فرض را برای تست محلی تنظیم کنیم.
    # در محیط کانتینر، بهتر است روی خطای 404 تکیه کنیم.

# ❌ حذف متغیر WEBHOOK_URL که به اشتباه برای نگهداری Secret Token استفاده می‌شد.
# WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "YOUR_SECRET_TOKEN") 


# --- وضعیت کاربر (User State) ---

USER_STATE: Dict[int, Dict[str, Any]] = {}
STEP_INPUT_DATE = "INPUT_DATE"
STEP_INPUT_TIME = "INPUT_TIME"
STEP_INPUT_CITY = "INPUT_CITY"
STEP_READY_TO_CALCULATE = "READY"


# --- توابع کمکی ---

def get_user_state(user_id: int) -> Dict[str, Any]:
    """دریافت وضعیت جاری کاربر یا مقداردهی اولیه آن."""
    if user_id not in USER_STATE:
        USER_STATE[user_id] = {
            "step": "START",
            "date_fa": None,
            "time_str": None,
            "city_name": None,
            "jdate_obj": None,
            "time_obj": None
        }
    return USER_STATE[user_id]

def reset_user_state(user_id: int) -> None:
    """بازنشانی وضعیت کاربر."""
    USER_STATE[user_id] = {
        "step": "START", 
        "date_fa": None, 
        "time_str": None, 
        "city_name": None, 
        "jdate_obj": None,
        "time_obj": None
    }

def build_chart_summary(chart_data: Dict[str, Any]) -> str:
    """ایجاد یک خلاصه زیبا از چارت برای کاربر."""
    if "error" in chart_data:
        return f"❌ خطای محاسباتی: {chart_data['error']}\nلطفاً دوباره امتحان کنید."
        
    summary = "✨ **خلاصه چارت نجومی شما** ✨\n\n"
    
    # اطلاعات ورودی
    state = USER_STATE.get(chart_data.get('user_id', 0), {})
    summary += f"_زمان تولد:_ {state.get('date_fa', 'نامشخص')} {state.get('time_str', 'نامشخص')}\n"
    summary += f"_محل تولد:_ {state.get('city_name', 'نامشخص')}\n\n"

    # موقعیت خورشید و ماه (نمونه از astrology_core)
    # ⚠️ توجه: این قسمت فرض می‌کند که ساختار chart_data را می‌دانید.
    # بهتر است از یک لیست سیارات مجاز استفاده کنید.
    for planet_key, data in chart_data.items():
        if isinstance(data, dict) and 'sign_fa' in data:
            name = data.get('name_fa', planet_key)
            sign = data['sign_fa']
            pos = data.get('position_str', 'نامشخص')
            summary += f"*{name}:* {pos} {sign} \n"
            
    summary += "\n---\n"
    summary += "⚠️ *توجه:* این یک چارت ساده (فقط خورشید و ماه) است. برای چارت کامل و تحلیل دقیق به بخش فروشگاه مراجعه کنید."
    
    return summary


# --- توابع هندلر ---

async def handle_start_command(chat_id: int) -> None:
    """هندلر دستور /start یا MAIN|WELCOME."""
    reset_user_state(chat_id)
    welcome_text = (
        "سلام! به ربات تخصصی آسترولوژی، سنگ‌شناسی و نمادشناسی خوش آمدید. "
        "لطفاً از منوی زیر، سرویس مورد نظر خود را انتخاب کنید\\."
    )
    await utils.send_message(BOT_TOKEN, chat_id, welcome_text, keyboards.main_menu_keyboard())

async def handle_callback_query(chat_id: int, callback_id: str, data: str) -> None:
    """هندلر کلیک‌های کیبورد اینلاین."""
    # 1. پاسخ به Callback Query برای حذف ساعت چرخان
    await utils.answer_callback_query(BOT_TOKEN, callback_id)

    # 2. تجزیه Callback Data: <MENU>|<SUBMENU>|<ACTION>
    parts = data.split('|')
    
    # اگر داده از ساختار مورد انتظار پیروی نمی‌کند، از آن چشم‌پوشی می‌کنیم یا به منوی اصلی باز می‌گردیم.
    if len(parts) < 3:
        await handle_start_command(chat_id)
        return

    menu, submenu, action = parts[0], parts[1], parts[2]
    
    response_text = "لطفاً یک گزینه را انتخاب کنید:"
    reply_markup = None
    state = get_user_state(chat_id)

    # مسیریابی منوی اصلی
    if menu == 'MAIN':
        if submenu == 'WELCOME':
            await handle_start_command(chat_id)
            return
        elif submenu == 'SERVICES':
            response_text = "بخش خدمات: چه نوع تحلیل یا ابزاری نیاز دارید؟"
            reply_markup = keyboards.services_menu_keyboard()
        elif submenu == 'SHOP':
            response_text = "بخش فروشگاه: برای سفارش چارت‌های کامل، تحلیل‌های شخصی و محصولات."
            reply_markup = keyboards.shop_menu_keyboard()
        elif submenu == 'SOCIALS':
            response_text = "شبکه‌های اجتماعی و لینک‌های ارتباطی ما:"
            reply_markup = keyboards.socials_menu_keyboard()
        elif submenu == 'ABOUT':
            response_text = "درباره ما: ما یک تیم تخصصی آسترولوژی و علوم باطنی هستیم. هدف ما ارائه دقیق‌ترین و شخصی‌سازی‌شده‌ترین تحلیل‌هاست."
            reply_markup = keyboards.back_to_main_menu_keyboard()

    # مسیریابی منوی خدمات
    elif menu == 'SERVICES':
        if submenu == 'ASTRO':
            if action == '0':
                response_text = "خدمات آسترولوژی: تولید چارت تولد یا ابزارهای دیگر."
                reply_markup = keyboards.astrology_menu_keyboard()
            elif action == 'CHART_INPUT':
                response_text = "لطفاً تاریخ تولد خود را به فرمت شمسی (مثلاً *1370/01/01*) ارسال کنید\\."
                reply_markup = keyboards.back_to_main_menu_keyboard()
                state['step'] = STEP_INPUT_DATE
            
        elif submenu == 'GEM':
            response_text = "خدمات سنگ‌شناسی:"
            reply_markup = keyboards.gem_menu_keyboard()
            
        # ... سایر زیرمنوها (SIGIL, HERB) ...

    # ارسال پاسخ نهایی
    # ⚠️ نیاز به utils.edit_message برای ویرایش پیام قبلی
    # فرض می‌کنیم utils.send_message در اینجا کافی است
    await utils.send_message(BOT_TOKEN, chat_id, response_text, reply_markup)

async def handle_text_message(chat_id: int, text: str) -> None:
    """هندلر پیام‌های متنی از کاربر."""
    state = get_user_state(chat_id)
    current_step = state['step']
    response_text = "ورودی نامعتبر. لطفاً مطابق درخواست قبلی، اطلاعات را وارد کنید."
    reply_markup = keyboards.back_to_main_menu_keyboard()

    if current_step == STEP_INPUT_DATE:
        jdate: Optional[JalaliDateTime] = utils.parse_persian_date(text)
        if jdate:
            state['date_fa'] = text
            state['jdate_obj'] = jdate
            state['step'] = STEP_INPUT_TIME
            response_text = "تاریخ تولد شما ثبت شد\\. حالا لطفاً ساعت تولد را به وقت محلی به فرمت *HH:MM* (مثلاً *08:30*) ارسال کنید\\."
        else:
            response_text = "فرمت تاریخ اشتباه است\\. لطفاً از فرمت *1370/01/01* استفاده کنید\\."

    elif current_step == STEP_INPUT_TIME:
        # بررسی فرمت زمان HH:MM
        try:
            # ⚠️ اصلاح: استفاده از datetime که در بالای فایل ایمپورت شد
            time_obj = datetime.datetime.strptime(text, "%H:%M").time()
            state['time_str'] = text
            state['time_obj'] = time_obj
            state['step'] = STEP_INPUT_CITY
            response_text = "ساعت تولد شما ثبت شد\\. در نهایت، لطفاً نام شهر محل تولد (مثلاً *تهران*) را ارسال کنید\\."
        except ValueError:
            response_text = "فرمت ساعت اشتباه است\\. لطفاً از فرمت *HH:MM* (مثلاً *08:30*) استفاده کنید\\."

    elif current_step == STEP_INPUT_CITY:
        city_name = text.strip()
        
        # 1. دریافت مختصات و منطقه زمانی (عملیات Blocking I/O که در utils آسنکرون شده است)
        await utils.send_message(BOT_TOKEN, chat_id, "⏳ در حال جستجوی شهر و منطقه زمانی شما\\...", None)
        # ⚠️ نیاز به چک کردن تابع get_coordinates_from_city در utils برای آسنکرون بودن
        lat, lon, tz = await utils.get_coordinates_from_city(city_name)
        
        if lat is None or lon is None:
            response_text = f"متأسفانه شهر *{city_name}* پیدا نشد\\. لطفاً نام شهر را با دقت بیشتری وارد کنید\\."
            state['step'] = STEP_INPUT_CITY # می‌مانیم تا دوباره تلاش کند
        else:
            state['city_name'] = city_name # ذخیره نام شهر
            
            # 2. آماده‌سازی داده‌های نهایی
            jdate: JalaliDateTime = state['jdate_obj']
            time_obj = state['time_obj']
            
            # ترکیب تاریخ و زمان شمسی
            dt_local = jdate.togregorian().replace(hour=time_obj.hour, minute=time_obj.minute, second=0)
            
            # اعمال منطقه زمانی و تبدیل به UTC
            # ⚠️ اصلاح: استفاده از pytz که در بالای فایل ایمپورت شد
            dt_local_with_tz = tz.localize(dt_local)
            birth_time_utc = dt_local_with_tz.astimezone(pytz.utc)
            
            # 3. محاسبه چارت (عملیات CPU-Bound)
            chart_data = astrology_core.calculate_natal_chart(birth_time_utc, lat, lon)
            chart_data['user_id'] = chat_id # برای نمایش خلاصه

            # 4. نمایش نتیجه و بازنشانی وضعیت
            response_text = build_chart_summary(chart_data)
            reply_markup = keyboards.main_menu_keyboard()
            reset_user_state(chat_id) # عملیات کامل شد

    # ارسال پاسخ نهایی
    await utils.send_message(BOT_TOKEN, chat_id, response_text, reply_markup)


# --- پیکربندی FastAPI ---

app = FastAPI()

# ⚠️ مسیر وب‌هوک به توکن ربات شما گره خورده است.
@app.post(f"/{BOT_TOKEN}")
async def webhook_handler(request: Request):
    """هندلر اصلی وب‌هوک تلگرام."""
    
    # ❌ حذف منطق چک کردن توکن مخفی:
    # if request.headers.get("x-telegram-bot-api-secret-token") != WEBHOOK_URL:
    #     raise HTTPException(status_code=403, detail="Invalid Secret Token")
    
    body = await request.json()
    
    # بررسی کنید که آیا به‌روزرسانی شامل پیام یا Callback Query است
    if 'message' in body:
        message = body['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        # هندل دستور /start
        if text.startswith('/start'):
            await handle_start_command(chat_id)
        # هندل پیام متنی عادی
        elif text and get_user_state(chat_id)['step'] != 'START':
            await handle_text_message(chat_id, text)
        # اگر کاربر در حالت START چیزی نوشت (به جز /start)
        else:
             await handle_start_command(chat_id)

    elif 'callback_query' in body:
        query = body['callback_query']
        chat_id = query['message']['chat']['id']
        callback_id = query['id']
        data = query['data']
        
        await handle_callback_query(chat_id, callback_id, data)
        
    return {"ok": True}

@app.get("/")
async def health_check():
    """بررسی سلامت سرویس."""
    return {"status": "ok", "message": "Bot is running. Webhook path is /<BOT_TOKEN>"}

