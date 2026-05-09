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

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_zodiac(ra_rad: float, dec_rad: float, body, observer) -> tuple[str, float]:
    """Convert geocentric ecliptic longitude to zodiac sign + degree."""
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return ZODIAC_SIGNS[sign_index], round(degree_in_sign, 2)


def get_moon_phase(observer) -> dict:
    """Return moon phase info: illumination %, phase name, cycle day."""
    moon = ephem.Moon(observer)
    illum = moon.phase

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    days_since_new = float(observer.date) - float(prev_new)
    cycle_fraction = days_since_new / cycle_length if cycle_length else 0

    if cycle_fraction < 0.0625:
        phase_name = "New Moon"
    elif cycle_fraction < 0.1875:
        phase_name = "Waxing Crescent"
    elif cycle_fraction < 0.3125:
        phase_name = "First Quarter"
    elif cycle_fraction < 0.4375:
        phase_name = "Waxing Gibbous"
    elif cycle_fraction < 0.5625:
        phase_name = "Full Moon"
    elif cycle_fraction < 0.6875:
        phase_name = "Waning Gibbous"
    elif cycle_fraction < 0.8125:
        phase_name = "Last Quarter"
    elif cycle_fraction < 0.9375:
        phase_name = "Waning Crescent"
    else:
        phase_name = "New Moon"

    return {
        "illumination_pct": round(illum, 1),
        "phase_name": phase_name,
        "cycle_day": round(days_since_new, 1),
        "cycle_fraction": round(cycle_fraction, 3),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    observer = ephem.Observer()
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    observer.pressure = 0
    observer.epoch = observer.date

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class(observer)
        sign, degree = ecliptic_to_zodiac(0, 0, body, observer)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "formatted": f"{degree:05.2f}° {sign}",
        }

    moon_phase = get_moon_phase(observer)

    return {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_utc": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "positions": positions,
        "moon_phase": moon_phase,
    }


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    date_str = data["date"]

    out_path = Path(__file__).resolve().parent.parent / "data" / f"transits_{date_str}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")
    return data


if __name__ == "__main__":
    main()
