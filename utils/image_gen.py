from PIL import Image, ImageDraw, ImageFont
import math
import os

def draw_horoscope_image(positions: dict, filename: str = None) -> str:
    if filename is None:
        filename = "horoscope.png"
    width, height = 800, 800
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    center = width // 2, height // 2
    radius = 300

    draw.ellipse((center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius), outline="black", width=3)

    try:
        font = ImageFont.truetype("Vazir-Regular.ttf", 24)
    except:
        font = ImageFont.load_default()

    for planet, degree in positions.items():
        angle = math.radians(degree)
        x = center[0] + radius * math.cos(angle - math.pi/2)
        y = center[1] + radius * math.sin(angle - math.pi/2)
        draw.text((x, y), planet, fill="black", font=font)

    # مسیر ذخیره
    path = os.path.join(os.getcwd(), filename)
    img.save(path)
    return path
