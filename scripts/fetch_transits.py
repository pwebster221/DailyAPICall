#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
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

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_zodiac(ra_rad, dec_rad, date):
    """Convert RA/Dec to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign": SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "absolute_degree": round(lon_deg, 2),
    }


def get_moon_phase(observer):
    """Return moon phase percentage and name."""
    moon = ephem.Moon(observer)
    phase_pct = moon.phase
    age = observer.date - ephem.previous_new_moon(observer.date)
    if age < 7.38:
        name = "Waxing Crescent" if phase_pct > 1 else "New Moon"
    elif age < 14.77:
        name = "Waxing Gibbous" if phase_pct > 50 else "First Quarter"
    elif age < 22.15:
        name = "Waning Gibbous" if phase_pct > 50 else "Full Moon"
    else:
        name = "Waning Crescent" if phase_pct < 50 else "Last Quarter"

    if phase_pct > 98:
        name = "Full Moon"
    elif phase_pct < 2:
        name = "New Moon"
    elif 48 < phase_pct < 52:
        if age < 14.77:
            name = "First Quarter"
        else:
            name = "Last Quarter"

    return {"percentage": round(phase_pct, 1), "phase_name": name}


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0

    positions = {}
    for name, body_class in PLANETS:
        body = body_class(observer)
        pos = ecliptic_to_zodiac(body.ra, body.dec, observer.date)
        positions[name] = pos

    moon_phase = get_moon_phase(observer)

    result = {
        "date": date_str,
        "utc_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "positions": positions,
        "moon_phase": moon_phase,
    }

    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"transits_{date_str}.json"
    output_file.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
