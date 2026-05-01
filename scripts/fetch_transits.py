#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import os
import sys
from datetime import datetime, timezone

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


def ecliptic_to_sign(lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign and degree within sign."""
    lon_deg = math.degrees(lon_rad)
    if lon_deg < 0:
        lon_deg += 360.0
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg - (sign_index * 30)
    return SIGNS[sign_index], round(degree_in_sign, 2)


def compute_moon_phase(observer: ephem.Observer) -> dict:
    """Compute lunar phase details."""
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)

    moon_lon = float(ephem.Ecliptic(moon).lon)
    sun_lon = float(ephem.Ecliptic(sun).lon)
    elongation = moon_lon - sun_lon
    if elongation < 0:
        elongation += 2 * math.pi
    cycle_fraction = elongation / (2 * math.pi)
    illumination = round(moon.phase, 1)

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

    prev_new = ephem.previous_new_moon(observer.date)
    day_of_cycle = round(float(observer.date - prev_new), 1)

    return {
        "phase_name": phase_name,
        "illumination_pct": illumination,
        "cycle_fraction": round(cycle_fraction, 3),
        "day_of_cycle": day_of_cycle,
    }


def fetch_transits(date_str: str | None = None) -> dict:
    """Calculate planetary positions for the given date (UTC noon)."""
    if date_str is None:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = f"{date_str} 12:00:00"

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class(observer)
        ecl = ephem.Ecliptic(body, epoch=observer.date)
        sign, degree = ecliptic_to_sign(float(ecl.lon))
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "absolute_degree": round(math.degrees(float(ecl.lon)), 2),
        }

    moon_phase = compute_moon_phase(observer)

    result = {
        "date": date_str,
        "computed_at_utc": "12:00:00",
        "positions": positions,
        "moon_phase": moon_phase,
    }

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"transits_{date_str}.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(target_date)
