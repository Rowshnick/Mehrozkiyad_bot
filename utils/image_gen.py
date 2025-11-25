# utils/image_gen.py
from PIL import Image, ImageDraw, ImageFont
import math

def draw_horoscope_image(positions: dict, filename: str = "horoscope.png") -> str:
    """ساخت تصویر هوروسکوپ حرفه‌ای"""
    width, height = 800, 800
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # فونت فارسی (باید مسیر فونت را درست کنید)
    try:
        font = ImageFont.truetype("Vazir-Regular.ttf", 24)
    except:
        font = ImageFont.load_default()

    # رسم دایره و بخش‌های اصلی
    center = width // 2, height // 2
    radius = 300
    draw.ellipse((center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius), outline="black", width=3)

    # رسم سیارات روی دایره
    for i, (planet, degree) in enumerate(positions.items()):
        angle = math.radians(degree)
        x = center[0] + radius * math.cos(angle - math.pi/2)
        y = center[1] + radius * math.sin(angle - math.pi/2)
        draw.text((x, y), planet, fill="black", font=font)

    # ذخیره تصویر
    image.save(filename)
    return filename
