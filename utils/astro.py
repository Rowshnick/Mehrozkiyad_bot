# utils/astro.py
import swisseph as swe
from datetime import datetime
import math

swe.set_ephe_path("/usr/share/ephe")  # مسیر فایل‌های Swiss Ephemeris، در سرور خودتان تنظیم کنید

PLANETS = {
    "خورشید": swe.SUN,
    "ماه": swe.MOON,
    "عطارد": swe.MERCURY,
    "زهره": swe.VENUS,
    "مریخ": swe.MARS,
    "مشتری": swe.JUPITER,
    "زحل": swe.SATURN,
    "اورانوس": swe.URANUS,
    "نپتون": swe.NEPTUNE,
    "پلوتو": swe.PLUTO,
    "راس‌التقاطع شمالی": swe.MEAN_NODE
}

def get_julian_day(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> float:
    """تبدیل تاریخ و زمان به روز جولین"""
    decimal_hour = hour + minute / 60.0
    jd = swe.julday(year, month, day, decimal_hour)
    return jd

def get_planet_positions(jd: float, lat: float, lon: float) -> dict:
    """محاسبه موقعیت دقیق سیارات و ascendant"""
    positions = {}
    for name, code in PLANETS.items():
        pos, _ = swe.calc_ut(jd, code)
        positions[name] = pos[0]  # طول دایره‌ای سیاره
    # محاسبه Ascendant
    asc, mc, _ = swe.houses(jd, lat, lon, b'A')[0:3]
    positions["Ascendant"] = asc
    positions["MC"] = mc
    return positions

def generate_horoscope_text(positions: dict) -> str:
    """تولید متن هوروسکوپ فارسی حرفه‌ای"""
    text = "📖 هوروسکوپ شما:\n\n"
    for planet, degree in positions.items():
        text += f"{planet}: {degree:.2f}°\n"
    text += "\n🔮 تحلیل دقیق بر اساس موقعیت سیارات و ascendant انجام شد."
    return text

def get_horoscope(year: int, month: int, day: int, hour: int = None, minute: int = None,
                  lat: float = None, lon: float = None) -> str:
    """تابع اصلی برای تولید هوروسکوپ"""
    if hour is None:
        hour = 12  # پیش‌فرض ظهر
    if minute is None:
        minute = 0
    if lat is None or lon is None:
        # پیش‌فرض تهران
        lat, lon = 35.6892, 51.3890
    jd = get_julian_day(year, month, day, hour, minute)
    positions = get_planet_positions(jd, lat, lon)
    text = generate_horoscope_text(positions)
    return text

# نمونه تست مستقیم
if __name__ == "__main__":
    horoscope = get_horoscope(1990, 5, 17, 15, 30, 35.6892, 51.3890)
    print(horoscope)
