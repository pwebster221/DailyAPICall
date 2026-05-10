#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using the ephem package."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

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

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_sign(ecliptic_lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign and degree within sign."""
    import math
    degrees = math.degrees(ecliptic_lon_rad)
    degrees = degrees % 360
    sign_index = int(degrees // 30)
    degree_in_sign = degrees % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date: datetime | None = None) -> dict:
    """Calculate planetary positions for the given date (default: today UTC)."""
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
        sign, degree = ecliptic_to_sign(float(ecl.lon))
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "absolute_degree": round(float(ecl.lon) * 180 / 3.14159265358979, 2),
        }

    return {
        "date": date.strftime("%Y-%m-%d"),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "positions": positions,
    }


def main():
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%Y-%m-%d")

    transits = fetch_transits(today)

    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"transits_{date_str}.json"

    with open(output_path, "w") as f:
        json.dump(transits, f, indent=2)

    print(f"Transit data saved to {output_path}")
    print(json.dumps(transits, indent=2))
    return transits


if __name__ == "__main__":
    main()
