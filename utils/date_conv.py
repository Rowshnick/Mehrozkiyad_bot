from persiantools.jdatetime import JalaliDate

def gregorian_to_jalali(year: int, month: int, day: int) -> dict:
    jd = JalaliDate.from_gregorian(year=year, month=month, day=day)
    return {"year": jd.year, "month": jd.month, "day": jd.day}

def jalali_to_gregorian(year: int, month: int, day: int) -> dict:
    gd = JalaliDate(year, month, day).to_gregorian()
    return {"year": gd.year, "month": gd.month, "day": gd.day}
