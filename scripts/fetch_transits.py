#!/usr/bin/env python3
"""Fetch geocentric planetary positions for today using PyEphem."""

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


def ecliptic_longitude(body, observer):
    """Return ecliptic longitude in degrees for a body."""
    body.compute(observer)
    ecl = ephem.Ecliptic(body)
    return math.degrees(ecl.lon)


def longitude_to_sign(lon_deg):
    """Convert ecliptic longitude to zodiac sign and degree."""
    sign_idx = int(lon_deg // 30) % 12
    degree = lon_deg % 30
    return ZODIAC_SIGNS[sign_idx], degree


def is_retrograde(body_cls, observer):
    """Detect retrograde by comparing position over 1-day interval."""
    if body_cls in (ephem.Sun, ephem.Moon):
        return False
    day_before = ephem.Date(observer.date - 1)
    obs_before = ephem.Observer()
    obs_before.date = day_before

    b1 = body_cls()
    b1.compute(obs_before)
    ecl1 = ephem.Ecliptic(b1)
    lon1 = math.degrees(ecl1.lon)

    b2 = body_cls()
    b2.compute(observer)
    ecl2 = ephem.Ecliptic(b2)
    lon2 = math.degrees(ecl2.lon)

    diff = lon2 - lon1
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    return diff < 0


def main():
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.date = ephem.Date(now_utc)

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls()
        lon = ecliptic_longitude(body, observer)
        sign, degree = longitude_to_sign(lon)
        retro = is_retrograde(body_cls, observer)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "longitude": round(lon, 2),
            "retrograde": retro,
        }

    result = {
        "date": date_str,
        "utc_time": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "positions": positions,
    }

    output_path = f"data/transits_{date_str}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
