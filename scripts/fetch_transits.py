#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import ephem

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
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


def ecliptic_to_zodiac(ra_radians: float, dec_radians: float, body, observer) -> tuple[str, float]:
    """Convert ecliptic longitude to zodiac sign and degree within sign."""
    ecl = ephem.Ecliptic(body)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return ZODIAC_SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date: datetime | None = None) -> dict:
    """Calculate planetary positions for a given date (default: today UTC)."""
    if date is None:
        date = datetime.now(timezone.utc)

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = ephem.Date(date)

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        lon_deg = math.degrees(float(ecl.lon))
        sign_index = int(lon_deg // 30)
        degree_in_sign = lon_deg % 30
        positions[name] = {
            "sign": ZODIAC_SIGNS[sign_index],
            "degree": round(degree_in_sign, 2),
            "absolute_degree": round(lon_deg, 2),
        }

    return {
        "date": date.strftime("%Y-%m-%d"),
        "positions": positions,
    }


def main():
    data = fetch_transits()
    date_str = data["date"]
    output_path = Path(__file__).parent.parent / "data" / f"transits_{date_str}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Transit data saved to {output_path}")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
