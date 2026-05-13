#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

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
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_sign(ra_rad, dec_rad, body, observer):
    """Convert body's position to ecliptic longitude, return sign + degree."""
    ecl = ephem.Ecliptic(body)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    degrees = int(degree_in_sign)
    minutes = int((degree_in_sign - degrees) * 60)
    seconds = int(((degree_in_sign - degrees) * 60 - minutes) * 60)
    return {
        "sign": SIGNS[sign_index],
        "degree": degrees,
        "minutes": minutes,
        "seconds": seconds,
        "absolute_degree": round(lon_deg, 4),
        "formatted": f"{degrees}°{minutes:02d}'{seconds:02d}\" {SIGNS[sign_index]}",
    }


def get_moon_phase(observer):
    """Calculate moon phase details."""
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)

    moon_ecl = ephem.Ecliptic(moon)
    sun_ecl = ephem.Ecliptic(sun)
    moon_lon = math.degrees(float(moon_ecl.lon))
    sun_lon = math.degrees(float(sun_ecl.lon))

    elongation = (moon_lon - sun_lon) % 360
    cycle_fraction = elongation / 360.0
    illumination = moon.phase

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

    day_of_cycle = round(cycle_fraction * 29.53)

    return {
        "phase_name": phase_name,
        "illumination": round(illumination, 1),
        "cycle_fraction": round(cycle_fraction, 3),
        "elongation": round(elongation, 2),
        "day_of_cycle": day_of_cycle,
    }


def fetch_transits(date_str=None):
    """Compute planetary positions for the given date (or today)."""
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )
    else:
        dt = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0)

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = dt.strftime("%Y/%m/%d %H:%M:%S")

    positions = {}
    for name, body_class in PLANETS:
        body = body_class(observer)
        pos = ecliptic_to_sign(body.ra, body.dec, body, observer)
        positions[name] = pos

    moon_phase = get_moon_phase(observer)

    result = {
        "date": dt.strftime("%Y-%m-%d"),
        "computed_at_utc": dt.isoformat(),
        "positions": positions,
        "moon_phase": moon_phase,
    }
    return result


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_str)

    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"transits_{data['date']}.json"

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
