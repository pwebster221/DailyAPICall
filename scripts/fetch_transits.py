#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem.

Standardised computation: Observer at 0°N/0°E, noon UTC, tropical zodiac.
Output saved to data/transits_YYYY-MM-DD.json
"""

import datetime
import json
import math
import os
import sys

import ephem

SIGNS = [
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


def ecliptic_to_tropical(body, observer):
    """Return tropical ecliptic longitude in degrees for *body*."""
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    return math.degrees(ecl.lon)


def degree_to_sign(deg):
    """Convert 0-360 ecliptic longitude to sign + degree string."""
    sign_idx = int(deg // 30)
    sign_deg = deg % 30
    minutes = int((sign_deg - int(sign_deg)) * 60)
    return {
        "sign": SIGNS[sign_idx],
        "degree": round(deg, 4),
        "formatted": f"{int(sign_deg)}°{minutes:02d}' {SIGNS[sign_idx]}",
    }


def moon_phase_info(observer):
    """Return lunar phase details for the observer date."""
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)

    moon_ecl = ephem.Ecliptic(moon, epoch=observer.date)
    sun_ecl = ephem.Ecliptic(sun, epoch=observer.date)
    elongation = math.degrees(moon_ecl.lon - sun_ecl.lon) % 360

    illumination = moon.phase

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = next_new - prev_new
    cycle_day = observer.date - prev_new
    fraction = cycle_day / cycle_length

    if fraction < 0.0625:
        phase_name = "New Moon"
    elif fraction < 0.1875:
        phase_name = "Waxing Crescent"
    elif fraction < 0.3125:
        phase_name = "First Quarter"
    elif fraction < 0.4375:
        phase_name = "Waxing Gibbous"
    elif fraction < 0.5625:
        phase_name = "Full Moon"
    elif fraction < 0.6875:
        phase_name = "Waning Gibbous"
    elif fraction < 0.8125:
        phase_name = "Last Quarter"
    elif fraction < 0.9375:
        phase_name = "Waning Crescent"
    else:
        phase_name = "Balsamic"

    cycle_day_int = int(cycle_day) + 1

    return {
        "phase_name": phase_name,
        "illumination_pct": round(illumination, 1),
        "cycle_day": cycle_day_int,
        "cycle_fraction": round(fraction, 3),
        "elongation": round(elongation, 2),
    }


def fetch_transits(date_str=None):
    """Compute positions for all planets on *date_str* (YYYY-MM-DD)."""
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.elevation = 0
    observer.date = f"{date_str} 12:00:00"

    positions = {}
    for name, cls in PLANETS:
        body = cls(observer)
        deg = ecliptic_to_tropical(body, observer)
        info = degree_to_sign(deg)
        info["planet"] = name
        positions[name] = info

    moon_info = moon_phase_info(observer)

    result = {
        "date": date_str,
        "observer": "0°N/0°E, noon UTC",
        "zodiac": "tropical",
        "engine": f"PyEphem {ephem.__version__}",
        "planets": positions,
        "moon_phase": moon_info,
    }
    return result


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    data = fetch_transits(date_str)

    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"transits_{date_str}.json")

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
