#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now_utc = now_utc.replace(hour=12)

    observer = ephem.Observer()
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0

    positions = {}
    for name, body_cls in PLANETS:
        body = body_cls()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        abs_degree = round(math.degrees(ecl.lon) % 360, 2)
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "absolute_degree": abs_degree,
            "formatted": f"{degree:.2f}° {sign}",
        }

    moon_phase = observer.date
    prev_new = ephem.previous_new_moon(moon_phase)
    next_new = ephem.next_new_moon(moon_phase)
    cycle_length = float(next_new - prev_new)
    days_since_new = float(moon_phase - prev_new)
    phase_pct = round((days_since_new / cycle_length) * 100, 1)

    if phase_pct < 3:
        phase_name = "New Moon"
    elif phase_pct < 25:
        phase_name = "Waxing Crescent"
    elif phase_pct < 28:
        phase_name = "First Quarter"
    elif phase_pct < 50:
        phase_name = "Waxing Gibbous"
    elif phase_pct < 53:
        phase_name = "Full Moon"
    elif phase_pct < 75:
        phase_name = "Waning Gibbous"
    elif phase_pct < 78:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "time_utc": now_utc.strftime("%H:%M:%S"),
        "planets": positions,
        "moon_phase": {
            "percent_of_cycle": phase_pct,
            "phase_name": phase_name,
            "illumination": round(days_since_new / cycle_length * 100, 1),
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
    print(f"\nSaved to {out_path}")
    return data


if __name__ == "__main__":
    main()
