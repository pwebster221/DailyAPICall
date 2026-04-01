#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
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
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_zodiac(ra_rad: float, dec_rad: float, body: ephem.Body) -> tuple[str, float]:
    """Convert ecliptic longitude to zodiac sign and degree within sign."""
    ecl = ephem.Ecliptic(body)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = ephem.Date(now_utc)

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        lon_deg = math.degrees(float(ecl.lon))
        sign_index = int(lon_deg // 30)
        degree_in_sign = lon_deg % 30
        positions[name] = {
            "sign": SIGNS[sign_index],
            "degree": round(degree_in_sign, 2),
            "longitude": round(lon_deg, 2),
        }

    moon_phase = observer.date
    prev_new = ephem.previous_new_moon(moon_phase)
    next_new = ephem.next_new_moon(moon_phase)
    lunation_length = float(next_new) - float(prev_new)
    days_since_new = float(moon_phase) - float(prev_new)
    lunar_day = days_since_new
    illumination = round(body.phase if name == "Pluto" else 0, 1)

    moon_body = ephem.Moon()
    moon_body.compute(observer)
    illumination = round(moon_body.phase, 1)

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_utc": now_utc.isoformat(),
        "positions": positions,
        "moon_phase": {
            "illumination_pct": illumination,
            "lunar_day": round(lunar_day, 1),
        },
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
