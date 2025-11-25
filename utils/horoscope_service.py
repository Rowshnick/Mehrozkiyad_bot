from .astro import get_julian_day, get_planet_positions
from .image_gen import draw_horoscope_image

def generate_horoscope_markdown(positions: dict) -> str:
    text = "📖 **ستاره‌شناسی شما (هوروسکوپ)**\n\n"
    for pl, deg in positions.items():
        text += f"- {pl}: {deg:.2f}°\n"
    text += "\n🔮 تحلیل کلی بر اساس موقعیت سیارات و صعودی (Ascendant)."
    return text

def get_horoscope_with_image(year: int, month: int, day: int,
                             hour: int = None, minute: int = None,
                             lat: float = None, lon: float = None):
    if hour is None:
        hour = 12
    if minute is None:
        minute = 0
    if lat is None or lon is None:
        lat, lon = 35.6892, 51.3890

    jd = get_julian_day(year, month, day, hour, minute)
    pos = get_planet_positions(jd, lat, lon)
    text = generate_horoscope_markdown(pos)
    img = draw_horoscope_image(pos)
    return text, img
