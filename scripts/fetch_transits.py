#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
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


def ecliptic_lon_to_zodiac(ra_rad, dec_rad, body, observer):
    """Convert equatorial coords to ecliptic longitude, then to sign + degree."""
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    whole = int(degree_in_sign)
    minutes = int((degree_in_sign - whole) * 60)
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 4),
        "formatted": f"{whole}°{minutes:02d}' {ZODIAC_SIGNS[sign_index]}",
        "absolute_degree": round(lon_deg, 4),
    }


def get_moon_phase(observer):
    """Return moon phase information."""
    moon = ephem.Moon(observer)
    phase_pct = moon.phase

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    cycle_fraction = (float(observer.date) - float(prev_new)) / cycle_length
    day_of_cycle = round(cycle_fraction * 29.53)

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
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "cycle_fraction": round(cycle_fraction, 3),
        "day_of_cycle": day_of_cycle,
    }


def fetch_transits(date_str=None):
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    observer = ephem.Observer()
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class(observer)
        info = ecliptic_lon_to_zodiac(body.ra, body.dec, body, observer)
        positions[name] = info

    moon_phase = get_moon_phase(observer)

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planets": positions,
        "moon_phase": moon_phase,
    }

    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"transits_{now_utc.strftime('%Y-%m-%d')}.json"
    output_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
