def get_healing_text():
    return "پیام درمانی: آرامش، تعادل و تمرکز برای امروز."

def get_suggestion(user_id: int, field: str) -> dict:
    fmap = {
        "stone": "تمرکز روی سنگ‌های انرژی‌بخش مثل کوارتز.",
        "herb": "استفاده از گیاهان درمانی مثل آرام‌بخش‌ها.",
        "mantra": "تکرار مانترای مثبت برای تمرکز ذهن.",
        "symbol": "نماد درمانی برای تعادل و ارتعاش انرژی."
    }
    text = fmap.get(field, "نگاهی به خودتان و درونتان بیندازید.")
    return {"text": f"{text}", "image_url": None}
