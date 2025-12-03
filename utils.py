import os
import datetime
import httpx
from persiantools import jdatetime
import pytz
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from typing import Optional

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# --- توابع Telegram ---
async def send_telegram_message(chat_id: int, text: str, parse_mode: str = "Markdown", keyboard: Optional[dict] = None):
    """تابع مرکزی برای ارسال پیام به تلگرام."""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if keyboard:
        payload["reply_markup"] = keyboard
        
    # تلگرام MarkdownV2 را ترجیح می دهد، برای جلوگیری از خطاهای پارس
    if parse_mode == "Markdown":
        # Escape کردن کاراکترهای خاص تلگرام برای MarkdownV2
        text = text.replace('.', '\.').replace('-', '\-').replace('(', '\)').replace(')', '\)').replace('|', '\|')
        payload["text"] = text
        payload["parse_mode"] = "MarkdownV2"
        
    try:
        MAX_RETRIES = 3
        # استفاده از client.wait برای httpx مناسب نیست. بجای آن از asyncio.sleep استفاده می‌کنیم.
        import asyncio
        
        for attempt in range(MAX_RETRIES):
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(TELEGRAM_API_URL, json=payload)
                if response.status_code == 429 and attempt < MAX_RETRIES - 1:
                    # Too Many Requests - صبر و تلاش مجدد
                    retry_after = 2 ** attempt
                    print(f"Rate limit hit. Retrying in {retry_after}s...")
                    await asyncio.sleep(retry_after) 
                    continue
                response.raise_for_status()
                return response.json()
        
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
        # تنظیم منطقه زمانی به تهران برای نمایش محلی
        tehran_tz = pytz.timezone('Asia/Tehran')
        local_dt = dt_utc.astimezone(tehran_tz)
        
        jdate = jdatetime.JalaliDateTime.from_gregorian(local_dt)
        # فرمت خروجی: "۱۴۰۳/۰۹/۱۱ - ۱۷:۳۰:۰۰ (به وقت تهران)"
        return jdate.strftime('%Y/%m/%d') + ' - ' + local_dt.strftime('%H:%M:%S') + ' (به وقت تهران)'
    except Exception as e:
        print(f"Error converting to shamsi: {e}")
        return f"خطا در تبدیل تاریخ: {e}"

def parse_shamsi_to_utc_datetime(shamsi_date_str: str) -> Optional[datetime.datetime]:
    """
    پارس کردن رشته تاریخ و زمان شمسی (YYYY/MM/DD HH:MM) و تبدیل به datetime UTC.
    """
    # الگوی تطابق: YYYY/MM/DD HH:MM (بدون ثانیه در گروه های regex)
    match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})\s+(\d{1,2}):(\d{1,2})', shamsi_date_str)
    
    if match:
        year, month, day, hour, minute = match.groups()
        
        try:
            # 1. ساخت شیء JalaliDateTime و تبدیل به میلادی
            jdate = jdatetime.JalaliDateTime(
                int(year), int(month), int(day), int(hour), int(minute), 0
            )
            dt_gregorian_naive = jdate.to_gregorian()
            
            # 2. تعریف منطقه زمانی محلی (تهران) برای ورودی
            local_tz = pytz.timezone('Asia/Tehran')
            local_dt = local_tz.localize(dt_gregorian_naive, is_dst=None)
            
            # 3. تبدیل به UTC (زمان جهانی)
            dt_utc = local_dt.astimezone(pytz.utc)
            return dt_utc
            
        except ValueError as e:
            print(f"Value Error in date parsing: {e}")
            return None # تاریخ یا زمان نامعتبر
    else:
        return None

async def get_coordinates_from_city(city_name: str) -> Optional[tuple[float, float]]:
    """
    دریافت عرض و طول جغرافیایی شهر با استفاده از Geopy (به صورت آسنکرون).
    """
    geolocator = Nominatim(user_agent="AstrologyBot")
    try:
        # **ترفند اصلی: استفاده از to_thread.run_sync برای اجرای کد مسدودکننده**
        async with httpx.AsyncClient() as client:
            # ما فراخوانی blocking را در یک Thread اجرا می کنیم تا Event Loop بلاک نشود.
            location = await client.to_thread.run_sync(
                geolocator.geocode, 
                f"{city_name}, Iran", # جستجو با تمرکز بر ایران
                timeout=10
            )
            
        if location:
            # Skyfield از (عرض جغرافیایی، طول جغرافیایی) استفاده می‌کند
            return location.latitude, location.longitude
        return None
        
    except GeocoderTimedOut:
        print(f"Geocoder request timed out for {city_name}.")
        return None
    except GeocoderServiceError as e:
        print(f"Geocoder Service Error for {city_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Geocoding Error for {city_name}: {e}")
        return None

