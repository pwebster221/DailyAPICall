#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using the ephem package."""

import ephem
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
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


def ecliptic_to_zodiac(ra_radians, dec_radians, body, observer):
    """Convert ecliptic longitude to zodiac sign and degree."""
    ecl = ephem.Ecliptic(body)
    lon_deg = float(ecl.lon) * 180.0 / ephem.pi
    sign_index = int(lon_deg / 30)
    degree_in_sign = lon_deg % 30
    return ZODIAC_SIGNS[sign_index], round(degree_in_sign, 2), round(lon_deg, 4)


def fetch_transits(date_str=None):
    now_utc = datetime.now(timezone.utc)
    if date_str:
        target = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )
    else:
        target = now_utc.replace(hour=12, minute=0, second=0, microsecond=0)

    observer = ephem.Observer()
    observer.date = ephem.Date(target)
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0

    date_label = target.strftime("%Y-%m-%d")
    positions = {}

    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        sign, degree, abs_lon = ecliptic_to_zodiac(body.ra, body.dec, body, observer)
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "absolute_longitude": abs_lon,
            "retrograde": body.name != "Sun" and body.name != "Moon" and hasattr(body, "earth_distance"),
        }

    for name in PLANETS:
        body = PLANETS[name]()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        lon_deg = float(ecl.lon) * 180.0 / ephem.pi

        if name not in ("Sun", "Moon"):
            tomorrow = ephem.Observer()
            tomorrow.date = observer.date + 1
            tomorrow.lat = observer.lat
            tomorrow.lon = observer.lon
            tomorrow.pressure = 0
            body_tomorrow = PLANETS[name]()
            body_tomorrow.compute(tomorrow)
            ecl_tomorrow = ephem.Ecliptic(body_tomorrow)
            lon_tomorrow = float(ecl_tomorrow.lon) * 180.0 / ephem.pi
            daily_motion = lon_tomorrow - lon_deg
            if daily_motion > 180:
                daily_motion -= 360
            elif daily_motion < -180:
                daily_motion += 360
            positions[name]["retrograde"] = daily_motion < 0
        else:
            positions[name]["retrograde"] = False

    result = {
        "date": date_label,
        "computed_utc": now_utc.isoformat(),
        "positions": positions,
    }

    output_dir = Path(__file__).resolve().parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"transits_{date_label}.json"
    output_file.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
