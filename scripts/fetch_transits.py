#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = {
    "Sun": ephem.Sun,
    "Moon": ephem.Moon,
    "Mercury": ephem.Mercury,
    "Venus": ephem.Venus,
    "Mars": ephem.Mars,
    "Jupiter": ephem.Jupiter,
    "Saturn": ephem.Saturn,
    "Uranus": ephem.Uranus,
    "Neptune": ephem.Neptune,
    "Pluto": ephem.Pluto,
}


def ecliptic_lon_to_zodiac(ra_rad, dec_rad, date):
    """Convert equatorial coords to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    deg = int(degree_in_sign)
    minutes = int((degree_in_sign - deg) * 60)
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "formatted": f"{deg}°{minutes:02d}' {ZODIAC_SIGNS[sign_index]}",
        "absolute_degree": round(lon_deg, 2),
    }


def fetch_transits(date_str=None):
    if date_str is None:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.elevation = 0
    observer.date = f"{date_str} 12:00:00"

    positions = {}
    for name, body_class in PLANETS.items():
        body = body_class()
        body.compute(observer)
        pos = ecliptic_lon_to_zodiac(body.ra, body.dec, observer.date)
        positions[name] = pos

    result = {
        "date": date_str,
        "epoch": "J2000",
        "type": "geocentric",
        "positions": positions,
    }

    output_path = f"data/transits_{date_str}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
