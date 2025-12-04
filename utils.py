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
import re

# ثابت‌ها
TELEGRAM_API_BASE = "https://api.telegram.org/bot"
NOMINATIN_USER_AGENT = "mehrozkiyad_astrology_bot"

# کلاینت HTTP آسنکرون (برای استفاده در bot_app)
client = httpx.AsyncClient()

# سرویس مکان‌یابی (به دلیل Blocking بودن، باید در thread اجرا شود)
geolocator = Nominatim(user_agent=NOMINATIN_USER_AGENT)

# --- توابع کمکی ---

def escape_markdown_v2(text: str) -> str:
    """
    Escape کردن کاراکترهای خاص مورد نیاز برای parse_mode=MarkdownV2 در تلگرام.
    کاراکترهایی که باید Escape شوند:
    _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    # لیست کامل کاراکترهایی که باید Escape شوند
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Escape با استفاده از عبارت با قاعده (Regex)
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# --- توابع ارتباطی تلگرام ---

async def send_message(bot_token: str, chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> None:
    """ارسال پیام به تلگرام به صورت آسنکرون با استفاده از MarkdownV2."""
    url = f"{TELEGRAM_API_BASE}{bot_token}/sendMessage"
    
    # اطمینان از Escape شدن متن برای سازگاری کامل با MarkdownV2
    escaped_text = escape_markdown_v2(text)
    
    payload = {
        "chat_id": chat_id,
        "text": escaped_text,
        "parse_mode": "MarkdownV2",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        # ارسال آسنکرون
        response = await client.post(url, json=payload, timeout=10)
        response.raise_for_status() # بررسی خطاهای HTTP مانند 4xx/5xx
    except httpx.HTTPError as e:
        # خطای رایج: متن Escape نشده یا طولانی است.
        print(f"HTTP error sending message: {e}. Response content: {getattr(e.response, 'text', 'N/A')}")
    except Exception as e:
        print(f"Unexpected error sending message: {e}")

async def answer_callback_query(bot_token: str, callback_query_id: str, text: Optional[str] = None) -> None:
    """پاسخ به Callback Query (برای حذف ساعت چرخان Loading یا نمایش پیام)."""
    url = f"{TELEGRAM_API_BASE}{bot_token}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_query_id,
    }
    if text:
        # متن پاسخ کوتاه است و نیازی به Escape پیچیده ندارد، اما باید Alert شود.
        payload["text"] = text
        payload["show_alert"] = True
        
    try:
        # ارسال آسنکرون
        await client.post(url, json=payload, timeout=5)
    except httpx.HTTPError as e:
        print(f"HTTP error answering callback: {e}")
    except Exception as e:
        print(f"Unexpected error answering callback: {e}")

# --- توابع پارس تاریخ و زمان ---

def parse_persian_date(date_str: str) -> Optional[JalaliDateTime]:
    """تبدیل رشته تاریخ شمسی (مثلاً 1370/01/01) به JalaliDateTime."""
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            year, month, day = map(int, parts)
            # JalaliDateTime به طور خودکار صحت تاریخ (مثلاً تعداد روزهای ماه) را بررسی می‌کند.
            return JalaliDateTime(year, month, day)
    except ValueError:
        # در صورت نامعتبر بودن فرمت یا مقادیر تاریخ
        return None
    return None

def find_timezone(city_name: str) -> Optional[pytz.tzinfo.BaseTzInfo]:
    """
    پیدا کردن منطقه زمانی بر اساس نام شهر.
    توجه: این تابع فقط بر اساس حدس زدن از نام شهر کار می‌کند و بسیار غیر قابل اعتماد است.
    برای دقت بالا، پس از Geocoding (lat, lon) باید از کتابخانه‌ای مانند `timezonefinder`
    استفاده شود که به دلیل محدودیت کتابخانه‌ها در این ماژول، در اینجا لحاظ نشده است.
    """
    city_name_lower = city_name.lower()
    
    # مناطق زمانی معروف در ایران
    if any(k in city_name_lower for k in ["tehran", "تهران", "iran", "ایران"]):
        return pytz.timezone('Asia/Tehran')
    
    # مناطق زمانی پایتخت‌های مهم
    tz_map = {
        'london': 'Europe/London', 'paris': 'Europe/Paris', 'berlin': 'Europe/Berlin',
        'dubai': 'Asia/Dubai', 'ankara': 'Europe/Istanbul', 'new york': 'America/New_York'
    }
    
    for keyword, tz_name in tz_map.items():
        if keyword in city_name_lower:
            return pytz.timezone(tz_name)

    # پیش‌فرض امن: Asia/Tehran (به دلیل فارسی بودن ربات، این پیش فرض معقول است)
    return pytz.timezone('Asia/Tehran')

# --- توابع جغرافیایی (Geocoding) ---

async def get_coordinates_from_city(city_name: str) -> Tuple[Optional[float], Optional[float], Optional[pytz.tzinfo.BaseTzInfo]]:
    """
    دریافت مختصات جغرافیایی (Lat/Lon) و منطقه زمانی (TimeZone) از نام شهر.
    این عملیات مسدودکننده (Blocking) است و در یک Thread جداگانه اجرا می‌شود.
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
            # خطاهایی مانند Timeout یا مشکل در شبکه
            print(f"Geocoding error for {city_name}: {e}")
            return None, None

    # اجرای تابع مسدودکننده در یک thread جداگانه (حل مشکل Blocking I/O در Async)
    lat, lon = await client.to_thread.run_sync(blocking_geocode)
    
    # پیدا کردن منطقه زمانی (بر اساس نام شهر، نه مختصات)
    tz = find_timezone(city_name)
    
    return lat, lon, tz
