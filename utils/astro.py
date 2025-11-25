import swisseph as swe
from datetime import datetime

# utils/astro.py - Example implementations for astro utilities.
from datetime import date
from persiantools.jdatetime import JalaliDate

def bot_intro():
    return (
        "🔰 این ربات خدمات آسترولوژی و راهنمایی انرژی ارائه می‌دهد.\n\n"
        "• طالع روزانه و طالع بر اساس تاریخ تولد\n"
        "• نماد/سنگ/گیاه شخصی‌سازی شده\n"
        "• پیشنهادات حوزه‌ای و چارت تولد\n\nبرای شروع از منوی اصلی استفاده کنید."
    )

def services_list():
    return (
        "🛠 خدمات:\n"
        "1. طالع‌بینی (امروز / تاریخ تولد)\n"
        "2. نماد شخصی (عکس + توضیحات)\n"
        "3. سنگ شخصی\n"
        "4. گیاه شخصی\n"
        "5. پیشنهادات حوزه‌ای (سلامت/ثروت/عشق/شغل/موفقیت)\n"
        "6. نمایش چارت تولد\n"
        "7. لینک‌های خرید زیورآلات مرتبط\n"
    )

def get_daily_horoscope():
    # simple deterministic stub - in real app you'd compute based on planetary positions
    today = date.today()
    return f"طالع روزانه برای {today.isoformat()}: روزی خوب برای تمرکز و برنامه‌ریزی."
    
def get_horoscope(day, month, year):
    jd = swe.julday(year, month, day)
    # نمونه ساده، شما می‌توانید تحلیل کامل اضافه کنید
    planets = ["خورشید", "ماه", "عطارد", "زهره", "مریخ"]
    positions = [round(jd % 30 + i, 2) for i, p in enumerate(planets)]
    text = "🪐 هوروسکوپ شما:\n"
    for planet, pos in zip(planets, positions):
        text += f"{planet}: {pos} درجه\n"
    return text

def get_personal_symbol(user_id):
    # Return a dict with text and image_url (placeholder)
    return {
        "text": f"نماد ویژه برای کاربر {user_id}: نشان‌دهنده تعادل و خلاقیت.",
        "image_url": "https://via.placeholder.com/512x512.png?text=Symbol"
    }

def get_personal_stone(user_id):
    return {
        "text": f"سنگ مناسب برای کاربر {user_id}: لاجورد (Lapis Lazuli) — تقویت شهود.",
        "image_url": "https://via.placeholder.com/512x512.png?text=Stone"
    }

def get_personal_plant(user_id):
    return {
        "text": f"گیاه پیشنهاد شده برای کاربر {user_id}: آلوئه‌ورا — تسهیل آرامش و پاکسازی.",
        "image_url": "https://via.placeholder.com/512x512.png?text=Plant"
    }

def get_birth_chart(user_id):
    # return an image url or text
    return {
        "text": f"چارت تولد کاربر {user_id} آماده است.",
        "image_url": "https://via.placeholder.com/800x600.png?text=Birth+Chart"
    }

def get_shop_links():
    # return list of (title, url)
    return [
        ("فروشگاه زیورآلات تهران", "https://example.com/jewelry"),
        ("اینستاگرام ما", "https://instagram.com/example"),
    ]
