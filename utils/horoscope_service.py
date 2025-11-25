from .astro import get_julian_day, get_planet_positions
from .image_gen import draw_horoscope_image

def generate_horoscope_markdown(positions: dict) -> str:
    """تولید متن هوروسکوپ فارسی حرفه‌ای با Markdown"""
    text = "📖 **هوروسکوپ شما**\n\n"
    for planet, degree in positions.items():
        text += f"- {planet}: {degree:.2f}°\n"
    text += "\n🔮 تحلیل دقیق بر اساس موقعیت سیارات و Ascendant انجام شد."
    return text

def get_horoscope_with_image(year: int, month: int, day: int,
                             hour: int = None, minute: int = None,
                             lat: float = None, lon: float = None):
    """تولید هوروسکوپ متن و تصویر"""
    if hour is None:
        hour = 12
    if minute is None:
        minute = 0
    if lat is None or lon is None:
        lat, lon = 35.6892, 51.3890  # تهران پیش‌فرض

    jd = get_julian_day(year, month, day, hour, minute)
    positions = get_planet_positions(jd, lat, lon)

    text = generate_horoscope_markdown(positions)
    image_file = draw_horoscope_image(positions)
    return text, image_file

# نمونه تست مستقیم
if __name__ == "__main__":
    text, img = get_horoscope_with_image(1990, 5, 17, 15, 30, 35.6892, 51.3890)
    print(text)
    print(f"تصویر ذخیره شد در: {img}")
  
