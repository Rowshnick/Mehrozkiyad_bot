import os
import datetime
import httpx
from persiantools import jdatetime
import pytz
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# --- توابع Telegram ---
async def send_telegram_message(chat_id: int, text: str, parse_mode: str = "Markdown", keyboard=None):
    """تابع مرکزی برای ارسال پیام به تلگرام."""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if keyboard:
        payload["reply_markup"] = keyboard
        
    try:
        # استفاده از Exponential Backoff برای مدیریت خطاهای موقت
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(TELEGRAM_API_URL, json=payload)
                if response.status_code == 429 and attempt < MAX_RETRIES - 1:
                    # Too Many Requests - صبر و تلاش مجدد
                    await client.wait(2 ** attempt) 
                    continue
                response.raise_for_status() # بررسی خطاهای HTTP
                return response.json()
        
        # اگر پس از تلاش‌های مکرر موفق نشدیم
        print(f"Telegram API Error after {MAX_RETRIES} attempts.")
        return {"ok": False, "description": "Too Many Requests (Rate Limit)"}

    except httpx.HTTPStatusError as e:
        print(f"Telegram API Error (Status {e.response.status_code}): {e.response.text}")
        return {"ok": False, "description": f"HTTP Error: {e.response.status_code}"}
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")
        return {"ok": False, "description": f"Internal Error: {e}"}


# --- توابع Date/Time و Location ---
def convert_to_shamsi_date(dt_utc: datetime.datetime) -> str:
    """تبدیل datetime میلادی (UTC) به رشته تاریخ و زمان شمسی فارسی."""
    try:
        # برای دقت بیشتر، تاریخ میلادی را به شیء jdatetime تبدیل می‌کنیم
        jdate = jdatetime.JalaliDateTime.from_gregorian(dt_utc)
        # فرمت خروجی: "۱۴۰۳/۰۹/۱۱ - ۱۷:۳۰:۰۰ (UTC)"
        return jdate.strftime('%Y/%m/%d') + ' - ' + jdate.strftime('%H:%M:%S') + ' (UTC)'
    except Exception as e:
        return f"خطا در تبدیل تاریخ: {e}"

def parse_shamsi_to_utc_datetime(shamsi_date_str: str) -> datetime.datetime or None:
    """
    پارس کردن رشته تاریخ و زمان شمسی (YYYY/MM/DD HH:MM) و تبدیل به datetime UTC.
    """
    # الگوی مورد انتظار: YYYY/MM/DD HH:MM:SS (یا با خط تیره) - ثانیه اختیاری
    # این الگو را کمی آزادتر می‌کنیم تا با مثال شما (که ثانیه ندارد) تطبیق یابد:
    # مثال: `۱۳۷۰/۰۵/۲۲، ۱۷:۳۰، تهران` -> ۱۳۷۰/۰۵/۲۲، ۱۷:۳۰
    match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})\s+(\d{1,2}):(\d{1,2})', shamsi_date_str)
    
    if match:
        year, month, day, hour, minute = match.groups()
        second = 0 # ثانیه را به صورت پیش‌فرض صفر می‌گیریم
        
        try:
            # ساخت شیء JalaliDateTime
            jdate = jdatetime.JalaliDateTime(
                int(year), int(month), int(day), int(hour), int(minute), int(second)
            )
            
            # تبدیل به datetime میلادی
            dt_gregorian = jdate.to_gregorian()
            
            # تنظیم منطقه زمانی به UTC (Skyfield باید با زمان UTC کار کند)
            return dt_gregorian.replace(tzinfo=datetime.UTC)
        except ValueError:
            return None # تاریخ نامعتبر
    else:
        return None

def get_coordinates_from_city(city_name: str) -> tuple[float, float] or None:
    """دریافت عرض و طول جغرافیایی شهر با استفاده از Geopy."""
    # Skyfield از (عرض جغرافیایی، طول جغرافیایی) استفاده می‌کند
    geolocator = Nominatim(user_agent="AstrologyBot")
    try:
        location = geolocator.geocode(city_name, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None
    except GeocoderTimedOut:
        print("Geocoder request timed out.")
        return None
    except GeocoderServiceError as e:
        print(f"Geocoder Service Error: {e}")
        return None
