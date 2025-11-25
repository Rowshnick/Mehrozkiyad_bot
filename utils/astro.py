import swisseph as swe
import math

PLANETS = {
    "خورشید": swe.SUN,
    "ماه": swe.MOON,
    "عطارد": swe.MERCURY,
    "زهره": swe.VENUS,
    "مریخ": swe.MARS,
    "مشتری": swe.JUPITER,
    "زحل": swe.SATURN,
    "اورانوس": swe.URANUS,
    "نپتون": swe.NEPTUNE,
    "پلوتو": swe.PLUTO,
    "راس‌التقاطع": swe.MEAN_NODE
}

def get_julian_day(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> float:
    decimal_hour = hour + minute / 60.0
    jd = swe.julday(year, month, day, decimal_hour)
    return jd

def get_planet_positions(jd: float, lat: float, lon: float) -> dict:
    positions = {}
    for name, code in PLANETS.items():
        pos, _ = swe.calc_ut(jd, code)
        positions[name] = pos[0]
    asc, mc, _ = swe.houses(jd, lat, lon, b'A')[0:3]
    positions["Ascendant"] = asc
    positions["MC"] = mc
    return positions
