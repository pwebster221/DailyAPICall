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


def ecliptic_to_zodiac(ra_rad, dec_rad, body, observer):
    """Convert equatorial coords to ecliptic longitude, return sign + degree."""
    ecl = ephem.Ecliptic(body)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign": SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "absolute_degree": round(lon_deg, 2),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    if date_str:
        now = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls()
        body.compute(observer)
        info = ecliptic_to_zodiac(body.ra, body.dec, body, observer)
        positions[name] = info

    moon = ephem.Moon()
    moon.compute(observer)
    moon_phase = round(moon.phase, 1)

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    cycle_fraction = (float(observer.date) - float(prev_new)) / cycle_length
    cycle_day = int(cycle_fraction * 29.5) + 1

    if cycle_fraction < 0.125:
        phase_name = "New Moon"
    elif cycle_fraction < 0.25:
        phase_name = "Waxing Crescent"
    elif cycle_fraction < 0.375:
        phase_name = "First Quarter"
    elif cycle_fraction < 0.5:
        phase_name = "Waxing Gibbous"
    elif cycle_fraction < 0.625:
        phase_name = "Full Moon"
    elif cycle_fraction < 0.75:
        phase_name = "Waning Gibbous"
    elif cycle_fraction < 0.875:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    result = {
        "date": now.strftime("%Y-%m-%d"),
        "time_utc": now.strftime("%H:%M:%S"),
        "positions": positions,
        "moon_phase": {
            "illumination": moon_phase,
            "phase_name": phase_name,
            "cycle_day": cycle_day,
            "cycle_fraction": round(cycle_fraction, 3),
        },
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    date_str = data["date"]

    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{date_str}.json"
    out_path.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
