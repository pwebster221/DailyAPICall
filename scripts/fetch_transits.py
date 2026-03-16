#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def ecliptic_longitude(body, observer):
    """Return ecliptic longitude in decimal degrees for a body."""
    body.compute(observer)
    ecl = ephem.Ecliptic(body)
    return math.degrees(float(ecl.lon))


def lon_to_sign_degree(lon_deg):
    """Convert ecliptic longitude (0-360) to sign + degree within sign."""
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def get_moon_phase(observer):
    """Return moon phase info."""
    moon = ephem.Moon(observer)
    moon.compute(observer)
    phase_pct = moon.phase

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new - prev_new)
    days_since_new = float(observer.date - prev_new)
    cycle_fraction = days_since_new / cycle_length

    if cycle_fraction < 0.125:
        phase_name = "New Moon" if cycle_fraction < 0.02 else "Waxing Crescent"
    elif cycle_fraction < 0.25:
        phase_name = "First Quarter"
    elif cycle_fraction < 0.375:
        phase_name = "Waxing Gibbous"
    elif cycle_fraction < 0.625:
        phase_name = "Full Moon" if 0.48 < cycle_fraction < 0.52 else "Waning Gibbous"
    elif cycle_fraction < 0.75:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    return {
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "days_since_new": round(days_since_new, 1),
        "next_new_moon": str(ephem.Date(next_new)),
    }


def check_retrograde(planet_class, observer):
    """Heuristic: compare position now vs 1 day later to detect retrograde."""
    obs_now = observer.copy()
    obs_later = observer.copy()
    obs_later.date = ephem.Date(obs_now.date + 1)

    body_now = planet_class()
    body_now.compute(obs_now)
    ecl_now = ephem.Ecliptic(body_now)
    lon_now = math.degrees(float(ecl_now.lon))

    body_later = planet_class()
    body_later.compute(obs_later)
    ecl_later = ephem.Ecliptic(body_later)
    lon_later = math.degrees(float(ecl_later.lon))

    diff = lon_later - lon_now
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360

    return diff < 0


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = f"{date_str} 12:00:00"

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        lon = ecliptic_longitude(body, observer)
        sign, degree = lon_to_sign_degree(lon)
        retrograde = False
        if name not in ("Sun", "Moon"):
            retrograde = check_retrograde(planet_class, observer)
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "longitude": round(lon, 4),
            "retrograde": retrograde,
        }

    moon_phase = get_moon_phase(observer)

    result = {
        "date": date_str,
        "positions": positions,
        "moon_phase": moon_phase,
    }

    output_dir = Path(__file__).resolve().parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"transits_{date_str}.json"
    output_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
