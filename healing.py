# utils/healing.py - simple suggestion generator for domains
def get_healing_text():
    return "پیام انرژی درمانی: آرامش، تعادل و تمرکز برای امروز."

def get_suggestion(user_id, field):
    field_map = {
        "سلامت": "تمرکز روی خواب منظم و تغذیه سالم.",
        "ثروت": "برنامه‌ریزی مالی هفتگی و صرفه‌جویی هدفمند.",
        "عشق": "ارتباط صادقانه و گوش دادن فعال به شریک زندگی.",
        "شغل": "تعیین اهداف کوتاه‌مدت و افزایش مهارت‌های تخصصی.",
        "موفقیت": "تفکیک کارها به وظایف کوچک و پیگیری منظم."
    }
    text = field_map.get(field, "پیشنهاد کلی: مراقبت از خود و برنامه‌ریزی.")
    return {"text": f"پیشنهاد برای حوزه {field}: {text}", "image_url": "https://via.placeholder.com/512x256.png?text=Suggestion"}
