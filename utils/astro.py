# utils/astro.py
import swisseph as swe
from datetime import datetime

# مسیر دیتای سوئیسیف
swe.set_ephe_path("/usr/share/ephe")

def get_horoscope(day: int, month: int, year: int) -> str:
    """
    تولید هوروسکوپ کامل بر اساس تاریخ تولد
    """
    try:
        jd = swe.julday(year, month, day)
        planets = {
            "خورشید": swe.SUN,
            "ماه": swe.MOON,
            "عطارد": swe.MERCURY,
            "زهره": swe.VENUS,
            "مریخ": swe.MARS,
            "مشتری": swe.JUPITER,
            "زحل": swe.SATURN,
            "اورانوس": swe.URANUS,
            "نپتون": swe.NEPTUNE,
            "پلوتو": swe.PLUTO
        }

        positions = {}
        for name, code in planets.items():
            pos = swe.calc_ut(jd, code)[0]
            positions[name] = round(pos[0], 2)  # درجه

        # متن هوروسکوپ ساده
        horoscope_text = "✨ هوروسکوپ شما:\n"
        for planet, degree in positions.items():
            horoscope_text += f"{planet}: {degree}°\n"

        horoscope_text += "\n📌 این تحلیل بر اساس موقعیت سیارات در زمان تولد شماست."
        return horoscope_text
    except Exception as e:
        return f"خطا در تولید هوروسکوپ: {e}"
        
