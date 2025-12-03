import os
import datetime
from skyfield.api import load, Topos, EarthSatellite, wgs84
from skyfield.framelib import ecliptic_frame
import numpy as np

# ایمپورت مطلق (اصلاح شده برای محیط دیپلوی تک‌دایرکتوری)
import data_lookup 

# تعریف Skyfield Loader و داده‌های دائمی
# این بخش فقط یک بار در هنگام راه‌اندازی برنامه (bot_app.py) فراخوانی می‌شود
eph = load('de421.bsp') # Ephemeris
ts = load.timescale()

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
        
        # تبدیل به مختصات دایرةالبروجی
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
    # **توجه: محاسبه دقیق Ascendant پیچیده است و به House System بستگی دارد.**
    # Skyfield به‌تنهایی این کار را نمی‌کند. اینجا فقط یک Placeholder می‌گذاریم.
    # برای محاسبه دقیق، باید از کتابخانه‌ای مانند Pyswisseph یا AstroPy با تابع محاسبه Houses استفاده کنید.
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
        
        if next_start_deg == 0:
            # آخرین نشانه (ماهی) تا 360 درجه ادامه دارد
            if lon >= start_deg:
                return ZODIAC_SIGNS[i]
        elif start_deg <= lon < next_start_deg:
            return ZODIAC_SIGNS[i]

    return data_lookup.ZODIAC_SIGNS[0] # در صورت خطای غیرمنتظره، حمل برگردانده شود.
