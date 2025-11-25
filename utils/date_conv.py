# utils/date_conv.py
from persiantools.jdatetime import JalaliDate

def gregorian_to_jalali(year: int, month: int, day: int) -> dict:
    """
    تبدیل تاریخ میلادی به شمسی
    ورودی: سال، ماه، روز میلادی
    خروجی: دیکشنری شامل سال، ماه، روز شمسی
    """
    try:
        jd = JalaliDate.from_gregorian(year=year, month=month, day=day)
        return {"year": jd.year, "month": jd.month, "day": jd.day}
    except Exception as e:
        raise ValueError(f"تبدیل میلادی به شمسی ناموفق بود: {e}")

def jalali_to_gregorian(year: int, month: int, day: int) -> dict:
    """
    تبدیل تاریخ شمسی به میلادی
    ورودی: سال، ماه، روز شمسی
    خروجی: دیکشنری شامل سال، ماه، روز میلادی
    """
    try:
        gd = JalaliDate(year, month, day).to_gregorian()
        return {"year": gd.year, "month": gd.month, "day": gd.day}
    except Exception as e:
        raise ValueError(f"تبدیل شمسی به میلادی ناموفق بود: {e}")
