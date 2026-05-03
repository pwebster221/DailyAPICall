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


def ecliptic_to_sign(lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree within sign."""
    lon_deg = math.degrees(lon_rad) % 360
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], degree_in_sign


def fetch_transits(date: datetime | None = None) -> dict:
    now = date or datetime.now(timezone.utc)
    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.elevation = 0
    observer.date = now

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_degree": round(math.degrees(ecl.lon) % 360, 2),
            "formatted": f"{degree:.0f}°{sign[:3]}",
        }

    moon_phase = observer.date
    prev_new = ephem.previous_new_moon(moon_phase)
    next_new = ephem.next_new_moon(moon_phase)
    cycle_length = float(next_new) - float(prev_new)
    cycle_fraction = (float(moon_phase) - float(prev_new)) / cycle_length
    illumination = round((1 - math.cos(2 * math.pi * cycle_fraction)) / 2 * 100, 1)

    if cycle_fraction < 0.0625:
        moon_phase_name = "New Moon"
    elif cycle_fraction < 0.1875:
        moon_phase_name = "Waxing Crescent"
    elif cycle_fraction < 0.3125:
        moon_phase_name = "First Quarter"
    elif cycle_fraction < 0.4375:
        moon_phase_name = "Waxing Gibbous"
    elif cycle_fraction < 0.5625:
        moon_phase_name = "Full Moon"
    elif cycle_fraction < 0.6875:
        moon_phase_name = "Waning Gibbous"
    elif cycle_fraction < 0.8125:
        moon_phase_name = "Last Quarter"
    elif cycle_fraction < 0.9375:
        moon_phase_name = "Waning Crescent"
    else:
        moon_phase_name = "New Moon"

    result = {
        "date": now.strftime("%Y-%m-%d"),
        "timestamp_utc": now.isoformat(),
        "planets": positions,
        "moon_phase": {
            "phase_name": moon_phase_name,
            "illumination_pct": illumination,
            "cycle_fraction": round(cycle_fraction, 4),
        },
    }
    return result


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=14, tzinfo=timezone.utc
        )
    else:
        dt = datetime.now(timezone.utc)

    data = fetch_transits(dt)

    out_path = Path(__file__).resolve().parent.parent / "data" / f"transits_{data['date']}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
