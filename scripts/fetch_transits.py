#!/usr/bin/env python3
"""Fetch geocentric planetary positions for a given date using PyEphem."""

import argparse
import json
import math
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
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_sign(ecl_lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign and degree within sign."""
    deg = math.degrees(ecl_lon_rad) % 360
    sign_idx = int(deg // 30)
    degree_in_sign = deg % 30
    return SIGNS[sign_idx], round(degree_in_sign, 2)


def fetch_transits(date_str: str | None = None) -> dict:
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0
    observer.date = date_str + " 12:00:00"

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        abs_degree = round(math.degrees(float(ecl.lon)) % 360, 2)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "abs_degree": abs_degree,
        }

    moon = ephem.Moon()
    moon.compute(observer)
    moon_phase = round(moon.phase, 1)
    prev_new = ephem.previous_new_moon(observer.date)
    lunar_day = round(float(observer.date - prev_new), 1)

    return {
        "date": date_str,
        "positions": positions,
        "moon_phase_pct": moon_phase,
        "lunar_day": lunar_day,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch planetary transits")
    parser.add_argument("--date", default=None, help="Date in YYYY-MM-DD format (default: today UTC)")
    args = parser.parse_args()

    data = fetch_transits(args.date)
    date_str = data["date"]

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{date_str}.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
