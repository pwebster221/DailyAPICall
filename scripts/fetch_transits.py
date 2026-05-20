#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using the ephem package."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

PLANETS = [
    ("Sun", ephem.Sun),
    ("Moon", ephem.Moon),
    ("Mercury", ephem.Mercury),
    ("Venus", ephem.Venus),
    ("Mars", ephem.Mars),
    ("Jupiter", ephem.Jupiter),
    ("Saturn", ephem.Saturn),
    ("Uranus", ephem.Uranus),
    ("Neptune", ephem.Neptune),
    ("Pluto", ephem.Pluto),
]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_sign(ecl_lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign and degree within sign."""
    deg = math.degrees(ecl_lon_rad) % 360
    sign_index = int(deg // 30)
    degree_in_sign = deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date: datetime | None = None) -> dict:
    now = date or datetime.now(timezone.utc)
    observer = ephem.Observer()
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0

    positions = {}
    for name, body_cls in PLANETS:
        body = body_cls()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_degree": round(math.degrees(ecl.lon) % 360, 2),
        }

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time_utc": now.strftime("%H:%M:%S"),
        "positions": positions,
    }


def main():
    data = fetch_transits()
    date_str = data["date"]

    output_path = Path(__file__).parent.parent / "data" / f"transits_{date_str}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2))

    print(f"Transit data saved to {output_path}")
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
