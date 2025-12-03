import datetime
from skyfield.api import load, Topos, Star, Earth, Angle, utc
from skyfield.framelib import ecliptic_frame

# مطمئن شوید که Skyfield فایل ephemeris را دانلود کرده است.
# این تابع فقط برای تست و جلوگیری از خطای ایمپورت/محاسبات قرار داده شده است.
try:
    # Skyfield با موفقیت فایل de421.bsp را در دیپلوی قبلی شما دانلود کرد.
    data = load('de421.bsp') 
    ts = load.timescale()
    earth = data['earth']
except Exception as e:
    print(f"WARNING: Skyfield data loading failed in placeholder: {e}")
    # اگر Skyfield fail کند، محاسبات Placeholder همچنان اجرا می‌شوند.


# ======================================================================
# تابع تطبیق درجه با نشانه زودیاک
# (این تابع باید از data_lookup.py استفاده کند، اما برای سادگی اینجا تعریف می‌شود)
# ======================================================================

def get_zodiac_sign(longitude_degrees: float) -> tuple[str, str]:
    """تبدیل درجه طول جغرافیایی به نام نشانه زودیاک فارسی و انگلیسی."""
    
    # لیست نشانه‌ها (Aries=0, Taurus=30, ...)
    ZODIAC_SIGNS = [
        (0, "Aries", "حمل"), (30, "Taurus", "ثور"), (60, "Gemini", "جوزا"), 
        (90, "Cancer", "سرطان"), (120, "Leo", "اسد"), (150, "Virgo", "سنبله"), 
        (180, "Libra", "میزان"), (210, "Scorpio", "عقرب"), (240, "Sagittarius", "قوس"), 
        (270, "Capricorn", "جدی"), (300, "Aquarius", "دلو"), (330, "Pisces", "حوت"),
    ]

    # محاسبه درجه در دایره 0 تا 360
    long_norm = longitude_degrees % 360

    # پیدا کردن نشانه
    for i in range(len(ZODIAC_SIGNS)):
        start_degree = ZODIAC_SIGNS[i][0]
        # درجه پایان نشانه فعلی، همان درجه شروع نشانه بعدی است (یا 360 برای حوت)
        end_degree = ZODIAC_SIGNS[(i + 1) % 12][0] if i < 11 else 360
        
        # اگر در محدوده معمولی باشد (مثل 100 درجه)
        if start_degree <= long_norm < end_degree:
            return ZODIAC_SIGNS[i][1], ZODIAC_SIGNS[i][2] # (انگلیسی، فارسی)
        
        # اگر محدوده از 360 عبور کند (که در این ساختار ساده اتفاق نمی افتد)

    # اگر چیزی پیدا نشد، Aries را برمی‌گردانیم.
    return "Aries", "حمل"

# ======================================================================
# تابع اصلی
# ======================================================================

def calculate_natal_chart(dt_utc: datetime.datetime, latitude: float, longitude: float, elevation: float = 0.0) -> dict:
    """
    محاسبه موقعیت سیارات اصلی (خورشید، ماه) در زمان و مکان مشخص.
    """
    
    # 1. تنظیمات زمان و مکان
    try:
        # تبدیل زمان UTC به شیء Skyfield Time
        t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second)
        # تنظیم مکان ناظر
        observer = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation)
    except NameError:
        # اگر Skyfield fail کند (به دلیل عدم دسترسی به ephemeris) یک خروجی ساده برمی‌گردانیم
        print("WARNING: Skyfield initialization failed. Returning placeholder data.")
        return {
            "Sun": {"longitude": "Failed", "sign_en": "Unknown", "sign_fa": "خورشید نامشخص"},
            "Moon": {"longitude": "Failed", "sign_en": "Unknown", "sign_fa": "ماه نامشخص"},
            "Ascendant": {"sign_en": "Unknown", "sign_fa": "طالع نامشخص"}
        }

    
    # 2. محاسبه سیارات اصلی (خورشید و ماه)
    planets = {
        "Sun": data['sun'],
        "Moon": data['moon'],
        # "Mercury": data['mercury'], # برای سادگی فعلاً حذف شده
        # "Venus": data['venus'],
        # "Mars": data['mars'],
    }
    
    natal_data = {}
    
    for name, planet in planets.items():
        # محاسبه موقعیت سیاره نسبت به ناظر (Geocentric) در مختصات دایره البروج (Ecliptic)
        astrometric = observer.at(t).observe(planet)
        lon, lat, distance = astrometric.frame_latlon(ecliptic_frame)
        
        lon_degrees = lon.degrees
        sign_en, sign_fa = get_zodiac_sign(lon_degrees)
        
        natal_data[name] = {
            "longitude": lon_degrees, # موقعیت دقیق (درجه)
            "sign_en": sign_en,
            "sign_fa": sign_fa,
            "latitude": lat.degrees,
            "distance": distance.km
        }

    # 3. محاسبه Ascendant (طلوعی)
    # محاسبه Ascendant نیاز به House System دارد که در Skyfield به سادگی در دسترس نیست.
    # این قسمت را فعلاً Placeholder نگه می‌داریم.
    natal_data["Ascendant"] = {
        "sign_en": "Placeholder",
        "sign_fa": "در حال پیاده‌سازی",
        "longitude": "N/A"
    }

    return natal_data
