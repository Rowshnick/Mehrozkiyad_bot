# ======================================================================
# ماژول اصلی محاسبات آسترولوژی
# این ماژول از Skyfield برای محاسبات نجومی دقیق استفاده می‌کند.
# ======================================================================

import datetime
from skyfield.api import load, Topos
from skyfield.timelib import Time
from typing import Dict, Any, Tuple

# ثابت‌ها
# تکمیل لیست سیارات اصلی برای چارت تولد (از خورشید تا پلوتو)
PLANETS = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'] 
DEGREES_PER_SIGN = 30
ZODIAC_SIGNS_FA = ["حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله", 
                    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت"]
PLANET_SYMBOLS_FA = {
    'sun': "خورشید ☉",
    'moon': "ماه ☽",
    'mercury': "عطارد ☿",
    'venus': "زهره ♀",
    'mars': "مریخ ♂",
    'jupiter': "مشتری ♃",
    'saturn': "زحل ♄",
    'uranus': "اورانوس ⛢",
    'neptune': "نپتون ♆",
    'pluto': "پلوتو ♇",
}

# داده‌های نجومی را بارگذاری کنید (یک بار در طول عمر برنامه)
try:
    # skyfield داده‌های ephemeris را در خود ذخیره می‌کند.
    # توصیه می‌شود از ephemeris‌های کاملتر مانند de430.bsp استفاده شود، اما de421.bsp رایج است.
    EPHEMERIS = load('de421.bsp')
except Exception as e:
    # برای جلوگیری از کرش در محیط‌هایی که دسترسی به شبکه محدود است
    print(f"Error loading ephemeris: {e}. Skyfield calculations will fail.")
    EPHEMERIS = None

def get_zodiac_position(lon: float) -> Tuple[str, str]:
    """تبدیل طول جغرافیایی (Ecliptic Longitude) به علامت زودیاک و درجه/دقیقه آن."""
    
    # اطمینان از قرار گرفتن طول جغرافیایی در دامنه ۰ تا ۳۶۰ درجه
    if lon < 0:
        lon += 360 
    if lon >= 360:
        lon %= 360

    sign_index = int(lon // DEGREES_PER_SIGN)
    degree_in_sign = lon % DEGREES_PER_SIGN
    
    sign_name = ZODIAC_SIGNS_FA[sign_index % 12]
    
    # محاسبه دقیقه از قسمت اعشاری درجه
    minutes = int((degree_in_sign - int(degree_in_sign)) * 60)
    
    # فرمت دهی درجه: 15° 30'
    degree_str = f"{int(degree_in_sign)}° {minutes:02d}'"
    
    return sign_name, degree_str

def calculate_natal_chart(birth_time_utc: datetime.datetime, lat: float, lon: float) -> Dict[str, Any]:
    """
    محاسبه موقعیت اجرام آسمانی برای زمان و مکان تولد.
    از محاسبات Topocentric (مشاهده از سطح زمین) برای دقت بالاتر استفاده می‌کند.
    
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
    # Skyfield زمان را بر اساس زمان پایتون (datetime.datetime) تفسیر می‌کند.
    t: Time = ts.utc(birth_time_utc) 
    
    # ۲. تعریف موقعیت مشاهده گر (Topocentric Observer)
    observer: Topos = EPHEMERIS['earth'] + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    chart_data: Dict[str, Any] = {}
    
    # ۳. محاسبه موقعیت اجرام (Topocentric Ecliptic Longitude)
    for planet_name in PLANETS:
        try:
            # مرجع جرم آسمانی
            planet_ephem = EPHEMERIS[planet_name]
            
            # مشاهده موقعیت جرم از دید ناظر
            position = observer.at(t).observe(planet_ephem)
            
            # محاسبه طول، عرض و فاصله در دستگاه مختصات دایرةالبروج (Ecliptic Longitude)
            # epoch='date' برای استفاده از Equinox تاریخ مشاهده به جای J2000
            lon_rad, lat_rad, distance = position.ecliptic_lonlat(epoch='date')
            
            # تبدیل به درجه
            lon_deg = lon_rad.degrees
            
            # محاسبه علامت زودیاک و درجه/دقیقه
            sign_name, degree_str = get_zodiac_position(lon_deg)
            
            chart_data[planet_name] = {
                "name_fa": PLANET_SYMBOLS_FA.get(planet_name, planet_name),
                "sign_fa": sign_name,
                "position_str": degree_str,
                "longitude_deg": round(lon_deg, 4),
            }
        
        except Exception as e:
            chart_data[planet_name] = {"error": f"Error calculating {planet_name}: {e}"}

    # ۴. محاسبه Ascendant و Houses (PLACEHOLDER)
    # محاسبه Ascendant و Houses به یک کتابخانه جداگانه House System نیاز دارد 
    # (مثلاً PyAstroCalc یا پیاده‌سازی دستی الگوریتم‌های Placidus/Koch).
    # این بخش باید در آینده تکمیل شود.
    # chart_data['ascendant'] = 'PLACEHOLDER: نیاز به House System' 
    # chart_data['houses'] = 'PLACEHOLDER: نیاز به House System'
    
    return chart_data

