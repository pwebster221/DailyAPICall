#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import os
from datetime import datetime, timezone

import ephem

SIGNS = [
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


def ecliptic_lon_to_sign(lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree within sign."""
    deg = math.degrees(lon_rad) % 360
    sign_idx = int(deg // 30)
    degree_in_sign = deg % 30
    return SIGNS[sign_idx], degree_in_sign


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now_utc = now_utc.replace(hour=12)

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer.date, epoch=observer.date)
        ecl = ephem.Ecliptic(body, epoch=observer.date)
        sign, degree = ecliptic_lon_to_sign(float(ecl.lon))
        abs_degree = math.degrees(float(ecl.lon)) % 360
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_degree": round(abs_degree, 2),
            "formatted": f"{sign} {int(degree)}°{int((degree % 1) * 60):02d}'",
        }

    moon_phase = observer.date - ephem.previous_new_moon(observer.date)
    cycle_length = ephem.next_new_moon(observer.date) - ephem.previous_new_moon(observer.date)
    cycle_fraction = moon_phase / cycle_length
    illumination = round((1 - math.cos(2 * math.pi * cycle_fraction)) / 2 * 100, 1)

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

    day_in_cycle = int(moon_phase) + 1

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_utc": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "planets": positions,
        "moon_phase": {
            "name": phase_name,
            "day": day_in_cycle,
            "illumination_pct": illumination,
            "cycle_fraction": round(cycle_fraction, 3),
        },
    }
    return result


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = fetch_transits(today)

    outpath = os.path.join(os.path.dirname(__file__), "..", "data", f"transits_{today}.json")
    outpath = os.path.normpath(outpath)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    with open(outpath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Transit data saved to {outpath}")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
