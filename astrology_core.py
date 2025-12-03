import os
import datetime
from pathlib import Path
from skyfield.api import load, Topos, Angle, Loader, EarthSatellite, wgs84
from skyfield.framelib import ecliptic_frame
import numpy as np

# ایمپورت مطلق (برای دسترسی به داده‌های ثابت مانند نشانه‌های زودیاک)
import data_lookup 

# =================================================================
# 1. راه‌اندازی Skyfield: لودر و Ephemeris (خودکار دانلود/لود ایمن)
# =================================================================

# تعریف مسیری برای کش کردن فایل های داده (مانند de421.bsp) در سرور.
# Skyfield به طور خودکار فایل را در این پوشه دانلود و ذخیره می کند.
# توجه: این مسیر باید در محیط ابری قابل نوشتن باشد.
data_dir = Path('./skyfield_temp_data')

# ایجاد شیء Loader
load_with_cache = Loader(data_dir)

# لود Ephemeris و Timescale با استفاده از Loader سفارشی
# اگر فایل de421.bsp در پوشه skyfield_temp_data وجود نداشته باشد، دانلود می‌شود.
try:
    eph = load_with_cache('de421.bsp')
    # ts (timescale) نیز باید با استفاده از همان شیء Loader ایجاد شود.
    ts = load_with_cache.timescale() 
except Exception as e:
    # در صورت بروز خطا در دانلود (مانند نبود دسترسی به اینترنت)، 
    # به لود استاندارد بازمی‌گردیم که فرض می‌کند فایل از قبل دستی آپلود شده است.
    print(f"Error loading ephemeris or timescale: {e}. Falling back to standard load.")
    # توجه: اگر خطا رخ دهد و فایل دستی هم موجود نباشد، برنامه از کار می‌افتد.
    eph = load('de421.bsp')
    ts = load.timescale()

# =================================================================
# 2. توابع اصلی
# =================================================================

def calculate_natal_chart(dt_utc: datetime.datetime, latitude: float, longitude: float, elevation: float = 0):
    """
    محاسبه موقعیت خورشید، ماه و Ascendant.
    
    توجه: این تابع فقط موقعیت سیارات را در دایرةالبروج محاسبه می‌کند. 
    محاسبه دقیق House System (مانند Placidus) نیاز به یک کتابخانه جداگانه دارد.
    """
    
    # تعریف زمان Skyfield
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second)
    
    # تعریف ناظر در زمین (محل تولد)
    location = Topos(latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation)
    
    # تعریف سیارات اصلی مورد نیاز
    planets = {
        'Sun': eph['sun'],
        'Moon': eph['moon'],
    }
    
    results = {}
    
    # 1. محاسبه موقعیت سیارات (طول دایرةالبروجی)
    for name, planet in planets.items():
        # مشاهده سیاره توسط ناظر (محل تولد)
        astrometric = location.at(t).observe(planet)
        
        # تبدیل به مختصات دایرةالبروجی (Ecliptic Coordinates)
        lon, lat, distance = astrometric.frame_latlon(ecliptic_frame)
        
        longitude_degrees = lon.degrees % 360
        
        # پیدا کردن نشانه زودیاک
        sign = get_zodiac_sign(longitude_degrees)
        
        results[name] = {
            'longitude': longitude_degrees,
            'sign_fa': sign[2], # نام فارسی نشانه
            'sign_en': sign[1],
        }

    # 2. محاسبه Ascendant (طالع یا صعودی)
    # **Placeholder: Skyfield به‌تنهایی این کار را نمی‌کند و نیاز به House System دارد.**
    results['Ascendant'] = {
        'longitude': "محاسبه_دقیق_لازم", 
        'sign_fa': "محاسبه_دقیق_لازم",
    }
    
    # 3. محاسبه Houseها (خانه دوم، پنجم، ششم، دهم)
    # **Placeholder: این بخش کاملا نیاز به کتابخانه House System دارد.**
    results['House_Cusps'] = {
        '2nd': {'sign_fa': "محاسبه_دقیق_لازم"},
        '5th': {'sign_fa': "محاسبه_دقیق_لازم"},
        '6th': {'sign_fa': "محاسبه_دقیق_لازم"},
        '10th': {'sign_fa': "محاسبه_دقیق_لازم"},
    }
    
    return results

def get_zodiac_sign(ecliptic_longitude: float):
    """پیدا کردن نشانه زودیاک بر اساس طول دایرةالبروجی (۰-۳۶۰)."""
    
    # اطمینان از قرارگیری در محدوده [0, 360)
    lon = ecliptic_longitude % 360
    
    # استفاده از data_lookup.ZODIAC_SIGNS
    ZODIAC_SIGNS = data_lookup.ZODIAC_SIGNS
    
    # لیست نشانه‌ها بر اساس درجه شروع مرتب شده است (ZODIAC_SIGNS)
    for i in range(len(ZODIAC_SIGNS)):
        start_deg, name_en, name_fa, element, color, symbol = ZODIAC_SIGNS[i]
        
        # درجه شروع نشانه بعدی
        next_start_deg = ZODIAC_SIGNS[(i + 1) % len(ZODIAC_SIGNS)][0]
        
        # منطق تعیین نشانه
        if next_start_deg == 0:
            # آخرین نشانه (ماهی) تا 360 درجه ادامه دارد
            if lon >= start_deg:
                return ZODIAC_SIGNS[i]
        elif start_deg <= lon < next_start_deg:
            return ZODIAC_SIGNS[i]

    return data_lookup.ZODIAC_SIGNS[0] # در صورت خطای غیرمنتظره، حمل برگردانده شود.
