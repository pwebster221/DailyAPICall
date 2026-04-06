#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
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


def ecliptic_to_zodiac(ecliptic_lon_rad: float) -> dict:
    """Convert ecliptic longitude (radians) to zodiac sign and degree."""
    deg = math.degrees(ecliptic_lon_rad) % 360
    sign_index = int(deg // 30)
    sign_degree = deg % 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(sign_degree, 2),
        "absolute_degree": round(deg, 2),
    }


def fetch_transits(date: datetime | None = None) -> dict:
    now = date or datetime.now(timezone.utc)
    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = ephem.Date(now)

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        info = ecliptic_to_zodiac(float(ecl.lon))
        info["ra"] = str(body.ra)
        info["dec"] = str(body.dec)
        positions[name] = info

    moon = ephem.Moon()
    moon.compute(observer)
    positions["Moon"]["phase"] = round(moon.phase, 1)
    prev_full = ephem.previous_full_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    days_since_full = float(observer.date - prev_full)
    positions["Moon"]["days_since_full"] = round(days_since_full, 1)
    if days_since_full <= 3.5:
        positions["Moon"]["phase_name"] = "Waning Gibbous"
    elif days_since_full <= 7.4:
        positions["Moon"]["phase_name"] = "Last Quarter"
    elif days_since_full <= 11:
        positions["Moon"]["phase_name"] = "Waning Crescent"
    elif days_since_full <= 14.8:
        positions["Moon"]["phase_name"] = "New Moon"
    else:
        positions["Moon"]["phase_name"] = "Waxing Crescent"

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time_utc": now.strftime("%H:%M:%S"),
        "positions": positions,
    }


if __name__ == "__main__":
    data = fetch_transits()
    date_str = data["date"]
    output_path = f"data/transits_{date_str}.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Transit data saved to {output_path}")
    print(json.dumps(data, indent=2))
