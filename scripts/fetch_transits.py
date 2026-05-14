#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem.

Standardized computation: Observer at 0°N, 0°E, noon UTC, tropical zodiac.
Outputs zodiac sign + degree for Sun through Pluto.
Saves to data/transits_YYYY-MM-DD.json.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

import ephem

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

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


def ecliptic_to_zodiac(ra_rad, dec_rad, body, observer):
    """Convert equatorial coords to ecliptic longitude, return sign + degree."""
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 4),
        "absolute_degree": round(lon_deg, 4),
        "degree_formatted": f"{int(degree_in_sign)}°{int((degree_in_sign % 1) * 60):02d}'",
    }


def get_moon_phase(observer):
    """Compute lunar phase info."""
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)

    moon_ecl = ephem.Ecliptic(moon, epoch=observer.date)
    sun_ecl = ephem.Ecliptic(sun, epoch=observer.date)
    elongation = math.degrees(float(moon_ecl.lon) - float(sun_ecl.lon)) % 360

    illumination = moon.phase

    if elongation < 45:
        phase_name = "New Moon"
    elif elongation < 90:
        phase_name = "Waxing Crescent"
    elif elongation < 135:
        phase_name = "First Quarter"
    elif elongation < 180:
        phase_name = "Waxing Gibbous"
    elif elongation < 225:
        phase_name = "Full Moon"
    elif elongation < 270:
        phase_name = "Waning Gibbous"
    elif elongation < 315:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    cycle_day = float(observer.date) - float(prev_new)
    cycle_fraction = cycle_day / cycle_length if cycle_length > 0 else 0

    return {
        "phase_name": phase_name,
        "illumination_pct": round(illumination, 1),
        "elongation": round(elongation, 2),
        "cycle_day": round(cycle_day, 1),
        "cycle_fraction": round(cycle_fraction, 3),
    }


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.elevation = 0
    observer.date = ephem.Date(now.replace(hour=12, minute=0, second=0, microsecond=0))

    positions = {}
    for name, body_class in PLANETS:
        body = body_class(observer)
        info = ecliptic_to_zodiac(body.ra, body.dec, body, observer)
        positions[name] = info

    moon_phase = get_moon_phase(observer)

    result = {
        "date": date_str,
        "computation": {
            "method": "PyEphem 4.2.1",
            "observer": "0°N, 0°E",
            "time": "noon UTC",
            "zodiac": "tropical",
        },
        "planets": positions,
        "moon_phase": moon_phase,
    }

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"transits_{date_str}.json")

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
