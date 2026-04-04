#!/usr/bin/env python3
"""Fetch geocentric planetary positions for today using PyEphem."""

import ephem
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ZODIAC_SIGNS = [
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


def ecliptic_to_zodiac(ra_rad, dec_rad, body, date):
    """Convert equatorial coords to ecliptic longitude, return sign + degree."""
    ecl = ephem.Ecliptic(body, epoch=date)
    lon_deg = float(ecl.lon) * 180.0 / 3.141592653589793
    sign_index = int(lon_deg / 30)
    degree_in_sign = lon_deg - sign_index * 30
    sign = ZODIAC_SIGNS[sign_index % 12]
    return sign, round(degree_in_sign, 2), round(lon_deg, 4)


def fetch_transits(date_str=None):
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    date_key = dt.strftime("%Y-%m-%d")
    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = dt.strftime("%Y/%m/%d %H:%M:%S")

    results = {"date": date_key, "computed_utc": str(observer.date), "planets": {}}

    for name, cls in PLANETS.items():
        body = cls()
        body.compute(observer)
        sign, degree, abs_lon = ecliptic_to_zodiac(body.ra, body.dec, body, observer.date)
        results["planets"][name] = {
            "sign": sign,
            "degree": degree,
            "absolute_longitude": abs_lon,
            "formatted": f"{degree:.2f}° {sign}",
        }

    moon = ephem.Moon()
    moon.compute(observer)
    results["moon_phase"] = round(moon.phase, 1)
    prev_full = ephem.previous_full_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    results["moon_phase_name"] = "Waning Gibbous" if moon.phase > 50 else "Waning Crescent"
    results["days_since_full"] = round(float(observer.date - prev_full), 1)

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{date_key}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
