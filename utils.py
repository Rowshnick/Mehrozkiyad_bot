# ======================================================================
# ماژول Utility Functions
# شامل توابع کمکی برای ارتباط با تلگرام، پارس تاریخ، و جغرافیایی (Geocoding).
# از httpx و client.to_thread.run_sync() برای جلوگیری از Blocking I/O استفاده می‌کند.
# ======================================================================

import httpx
import datetime
import pytz
from persiantools.jdatetime import JalaliDateTime
from geopy.geocoders import Nominatim
from geopy.location import Location
from typing import Optional, Tuple, Dict, Any, Callable

# ثابت‌ها
TELEGRAM_API_BASE = "https://api.telegram.org/bot"
NOMINATIM_USER_AGENT = "mehrozkiyad_astrology_bot"

# کلاینت HTTP آسنکرون (برای استفاده در bot_app)
client = httpx.AsyncClient()

# سرویس مکان‌یابی (به دلیل Blocking بودن، باید در thread اجرا شود)
geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT)

# --- توابع ارتباطی تلگرام ---

async def send_message(bot_token: str, chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> None:
    """ارسال پیام به تلگرام به صورت آسنکرون."""
    url = f"{TELEGRAM_API_BASE}{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "MarkdownV2",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        # ارسال آسنکرون
        await client.post(url, json=payload)
    except httpx.HTTPError as e:
        print(f"HTTP error sending message: {e}")
    except Exception as e:
        print(f"Unexpected error sending message: {e}")

async def answer_callback_query(bot_token: str, callback_query_id: str, text: Optional[str] = None) -> None:
    """پاسخ به Callback Query (برای حذف ساعت چرخان Loading)."""
    url = f"{TELEGRAM_API_BASE}{bot_token}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_query_id,
    }
    if text:
        payload["text"] = text
        payload["show_alert"] = True
        
    try:
        # ارسال آسنکرون
        await client.post(url, json=payload)
    except httpx.HTTPError as e:
        print(f"HTTP error answering callback: {e}")

# --- توابع پارس تاریخ و زمان ---

def parse_persian_date(date_str: str) -> Optional[JalaliDateTime]:
    """تبدیل رشته تاریخ شمسی (مثلاً 1370/01/01) به JalaliDateTime."""
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            year, month, day = map(int, parts)
            return JalaliDateTime(year, month, day)
    except ValueError:
        return None
    return None

def find_timezone(city_name: str) -> Optional[pytz.tzinfo.BaseTzInfo]:
    """پیدا کردن منطقه زمانی بر اساس نام شهر (PLACEHOLDER برای منطق دقیق)"""
    # این تابع باید در یک دیتابیس یا سرویس محلی شهر-منطقه زمانی جستجو کند.
    # برای جلوگیری از خطا، یک منطقه زمانی پیش‌فرض برمی‌گرداند.
    try:
        # برای ایران، تهران را به عنوان پیش فرض در نظر می‌گیریم.
        if "تهران" in city_name or "tehran" in city_name.lower():
            return pytz.timezone('Asia/Tehran')
        
        # جستجو در مناطق زمانی معروف
        for tz_name in pytz.common_timezones:
            if city_name.lower() in tz_name.lower():
                return pytz.timezone(tz_name)
    except Exception:
        pass
        
    # پیش‌فرض امن: Asia/Tehran
    return pytz.timezone('Asia/Tehran')

# --- توابع جغرافیایی (Geocoding) ---

async def get_coordinates_from_city(city_name: str) -> Tuple[Optional[float], Optional[float], Optional[pytz.tzinfo.BaseTzInfo]]:
    """
    دریافت مختصات جغرافیایی (Lat/Lon) و منطقه زمانی (TimeZone) از نام شهر.
    این عملیات مسدودکننده (Blocking) است و باید در یک Thread جداگانه اجرا شود.
    """
    
    def blocking_geocode() -> Tuple[Optional[float], Optional[float]]:
        """عملیات Geocoding مسدودکننده با geopy."""
        try:
            # مهلت زمانی (Timeout) برای جلوگیری از مسدود شدن طولانی
            location: Optional[Location] = geolocator.geocode(city_name, timeout=5)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            print(f"Geocoding error for {city_name}: {e}")
            return None, None

    # اجرای تابع مسدودکننده در یک thread جداگانه (حل مشکل Blocking I/O)
    lat, lon = await client.to_thread.run_sync(blocking_geocode)
    
    # پیدا کردن منطقه زمانی (به دلیل عدم پشتیبانی geopy از Timezone در همه سرویس‌ها)
    tz = find_timezone(city_name)
    
    return lat, lon, tz
