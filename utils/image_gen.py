# utils/image_gen.py
from PIL import Image, ImageDraw, ImageFont
import io

def generate_horoscope_image(horoscope_text: str, width=800, height=1000) -> bytes:
    """
    تولید عکس هوروسکوپ با متن فارسی
    خروجی: بایت برای ارسال در تلگرام
    """
    # ایجاد بوم سفید
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # فونت فارسی (فونت یک مسیر معتبر به ttf)
    try:
        font = ImageFont.truetype("fonts/Vazir.ttf", 28)
    except:
        font = ImageFont.load_default()

    # حاشیه و فاصله خطوط
    x_margin = 40
    y_margin = 40
    line_height = 40

    # تقسیم متن به خطوط
    lines = horoscope_text.split("\n")
    y_text = y_margin
    for line in lines:
        draw.text((x_margin, y_text), line, fill=(0, 0, 0), font=font)
        y_text += line_height

    # تبدیل به بایت
    byte_arr = io.BytesIO()
    img.save(byte_arr, format="PNG")
    byte_arr.seek(0)
    return byte_arr.getvalue()
