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


def ecliptic_to_zodiac(ra_rad, dec_rad, date):
    """Convert RA/Dec to ecliptic longitude, then to sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], degree_in_sign, lon_deg


def get_moon_phase(observer):
    """Return moon phase info: illumination %, age, and phase name."""
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)

    moon_ecl = ephem.Ecliptic(ephem.Equatorial(moon.ra, moon.dec, epoch=observer.date))
    sun_ecl = ephem.Ecliptic(ephem.Equatorial(sun.ra, sun.dec, epoch=observer.date))

    elongation = math.degrees(float(moon_ecl.lon) - float(sun_ecl.lon)) % 360

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    age = float(observer.date) - float(prev_new)
    cycle_fraction = age / cycle_length if cycle_length else 0

    illumination = moon.phase

    if cycle_fraction < 0.0375:
        phase_name = "New Moon"
    elif cycle_fraction < 0.2125:
        phase_name = "Waxing Crescent"
    elif cycle_fraction < 0.2875:
        phase_name = "First Quarter"
    elif cycle_fraction < 0.4625:
        phase_name = "Waxing Gibbous"
    elif cycle_fraction < 0.5375:
        phase_name = "Full Moon"
    elif cycle_fraction < 0.7125:
        phase_name = "Waning Gibbous"
    elif cycle_fraction < 0.7875:
        phase_name = "Last Quarter"
    elif cycle_fraction < 0.9625:
        phase_name = "Waning Crescent"
    else:
        phase_name = "Balsamic"

    day_of_cycle = int(age) + 1

    return {
        "illumination_pct": round(illumination, 1),
        "elongation": round(elongation, 2),
        "phase_name": phase_name,
        "day_of_cycle": day_of_cycle,
        "cycle_fraction": round(cycle_fraction, 3),
    }


def fetch_transits(date_str=None):
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )
    date_label = now_utc.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")

    positions = {}
    for name, body_cls in PLANETS:
        body = body_cls(observer)
        sign, degree, abs_lon = ecliptic_to_zodiac(body.ra, body.dec, observer.date)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_longitude": round(abs_lon, 2),
            "formatted": f"{degree:.0f}°{sign[:3]} ({sign} {degree:.2f}°)",
        }

    moon_phase = get_moon_phase(observer)

    result = {
        "date": date_label,
        "computed_utc": now_utc.isoformat(),
        "planets": positions,
        "moon_phase": moon_phase,
    }

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{date_label}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
