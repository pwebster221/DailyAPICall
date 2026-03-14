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


def ecliptic_to_sign(lon_rad: float) -> dict:
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    lon_deg = math.degrees(lon_rad) % 360
    sign_idx = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign": SIGNS[sign_idx],
        "degree": round(degree_in_sign, 2),
        "absolute_degree": round(lon_deg, 2),
    }


def fetch_transits(date: datetime | None = None) -> dict:
    now = date or datetime.now(timezone.utc)
    observer = ephem.Observer()
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")
    observer.pressure = 0
    observer.epoch = ephem.J2000

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        positions[name] = ecliptic_to_sign(float(ecl.lon))

    moon = ephem.Moon()
    moon.compute(observer)
    positions["Moon"]["phase_pct"] = round(moon.phase, 1)

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    day_in_cycle = float(observer.date) - float(prev_new)
    cycle_fraction = day_in_cycle / cycle_length

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
        phase_name = "Balsamic"

    return {
        "date": now.strftime("%Y-%m-%d"),
        "utc_time": now.strftime("%H:%M:%S UTC"),
        "moon_phase": phase_name,
        "positions": positions,
    }


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
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
