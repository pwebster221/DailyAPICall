#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
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

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_zodiac(ra_radians, dec_radians, body, observer):
    """Convert a body's position to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(body)
    lon_deg = float(ecl.lon) * 180.0 / ephem.pi
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "abs_degree": round(lon_deg, 2),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    if date_str:
        now = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")

    positions = {}
    for name, planet_class in PLANETS:
        body = planet_class()
        body.compute(observer)
        pos = ecliptic_to_zodiac(body.ra, body.dec, body, observer)
        positions[name] = pos

    moon = ephem.Moon()
    moon.compute(observer)
    phase_pct = moon.phase

    prev_new = ephem.previous_new_moon(observer.date)
    moon_age_days = observer.date - prev_new

    return {
        "date": now.strftime("%Y-%m-%d"),
        "computed_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planets": positions,
        "moon_phase": {
            "illumination_pct": round(phase_pct, 1),
            "age_days": round(float(moon_age_days), 1),
        },
    }


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"transits_{data['date']}.json"
    out_file.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
