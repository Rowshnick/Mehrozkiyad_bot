# ======================================================================
# ماژول اصلی محاسبات آسترولوژی
# این ماژول از Skyfield برای محاسبات نجومی دقیق استفاده می‌کند.
# وضعیت: PLACEHOLDER عملیاتی - فقط موقعیت‌های خورشید و ماه را محاسبه می‌کند.
# ======================================================================

import datetime
from skyfield.api import load, Topos
from skyfield.timelib import Time
from typing import Dict, Any, Tuple

# ثابت‌ها
PLANETS = ['sun', 'moon'] # در آینده باید تکمیل شود: 'mercury', 'venus', 'mars', ...
DEGREES_PER_SIGN = 30
ZODIAC_SIGNS_FA = ["حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله", 
                    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت"]

# داده‌های نجومی را بارگذاری کنید (یک بار در طول عمر برنامه)
try:
    # skyfield داده‌های ephemeris را در خود ذخیره می‌کند.
    EPHEMERIS = load('de421.bsp')
except Exception as e:
    # برای جلوگیری از کرش در محیط‌هایی که دسترسی به شبکه محدود است
    print(f"Error loading ephemeris: {e}")
    EPHEMERIS = None

def get_zodiac_position(lon: float) -> Tuple[str, str]:
    """تبدیل طول جغرافیایی (Longitude) به علامت زودیاک و درجه/دقیقه آن."""
    if lon < 0:
        lon += 360 # طول‌های منفی را به دامنه ۰ تا ۳۶۰ می‌برد

    sign_index = int(lon // DEGREES_PER_SIGN)
    degree_in_sign = lon % DEGREES_PER_SIGN
    
    sign_name = ZODIAC_SIGNS_FA[sign_index % 12]
    
    # فرمت دهی درجه: 15° 30'
    degree_str = f"{int(degree_in_sign)}° {int((degree_in_sign - int(degree_in_sign)) * 60):02d}'"
    
    return sign_name, degree_str

def calculate_natal_chart(birth_time_utc: datetime.datetime, lat: float, lon: float) -> Dict[str, Any]:
    """
    محاسبه موقعیت اجرام آسمانی برای زمان و مکان تولد.
    
    Args:
        birth_time_utc: زمان تولد به وقت UTC (بهبود یافته از utils).
        lat: عرض جغرافیایی.
        lon: طول جغرافیایی.
        
    Returns:
        دیکشنری شامل موقعیت اجرام آسمانی.
    """
    
    if EPHEMERIS is None:
        return {"error": "منابع نجومی (Ephemeris) بارگذاری نشده‌اند. لطفاً اتصال شبکه را بررسی کنید."}
        
    # ۱. تعریف زمان (Time)
    ts = load.timescale()
    t: Time = ts.utc(birth_time_utc)
    
    # ۲. تعریف موقعیت مشاهده گر (Observer)
    observer: Topos = EPHEMERIS['earth'] + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    chart_data: Dict[str, Any] = {}
    
    # ۳. محاسبه موقعیت اجرام (فقط خورشید و ماه برای Placeholder)
    for planet_name in PLANETS:
        # اجرام skyfield
        planet_ephem = EPHEMERIS[planet_name]
        
        # محاسبه موقعیت ژئوسنتریک در دایرةالبروج (ecliptic)
        astrometric = observer.at(t).observe(planet_ephem)
        # lon, lat, dist = astrometric.ecliptic_xyz(epoch='date').au 
        
        # محاسبه طول دایرةالبروجی (Ecliptic Longitude)
        lon_rad, lat_rad, distance = astrometric.ecliptic_using(t).frame.ecliptic_xyz(t, center=399, target=0, observer=observer)
        
        # تبدیل رادیان به درجه
        lon_deg = lon_rad.degrees
        
        # محاسبه علامت زودیاک
        sign_name, degree_str = get_zodiac_position(lon_deg)
        
        chart_data[planet_name] = {
            "sign_fa": sign_name,
            "position_str": degree_str,
            "longitude_deg": round(lon_deg, 4),
            "name_fa": f"خورشید ☉" if planet_name == 'sun' else f"ماه ☽"
            # در آینده باید فازهای ماه، سرعت، و سایر پارامترها اضافه شوند
        }

    # ۴. محاسبه Ascendant و Houses (PLACEHOLDER - نیاز به کتابخانه House System)
    # chart_data['ascendant'] = 'PLACEHOLDER' 
    # chart_data['houses'] = 'PLACEHOLDER'
    
    return chart_data
