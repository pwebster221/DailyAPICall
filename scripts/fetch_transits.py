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
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_sign(ra_rad, dec_rad, date):
    """Convert RA/Dec to ecliptic longitude, then to sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], degree_in_sign, lon_deg


def get_moon_phase(observer):
    """Return moon illumination percentage and phase name."""
    moon = ephem.Moon(observer)
    illum = moon.phase

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    days_since_new = float(observer.date) - float(prev_new)
    phase_pct = days_since_new / cycle_length

    if phase_pct < 0.125:
        name = "New Moon"
    elif phase_pct < 0.25:
        name = "Waxing Crescent"
    elif phase_pct < 0.375:
        name = "First Quarter"
    elif phase_pct < 0.5:
        name = "Waxing Gibbous"
    elif phase_pct < 0.625:
        name = "Full Moon"
    elif phase_pct < 0.75:
        name = "Waning Gibbous"
    elif phase_pct < 0.875:
        name = "Last Quarter"
    else:
        name = "Waning Crescent"

    return illum, name


def main():
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")

    positions = []
    for name, cls in PLANETS:
        body = cls(observer)
        sign, degree, abs_lon = ecliptic_to_sign(body.ra, body.dec, observer.date)
        deg_int = int(degree)
        minutes = int((degree - deg_int) * 60)

        positions.append({
            "planet": name,
            "sign": sign,
            "degree": round(degree, 2),
            "degree_formatted": f"{deg_int}°{minutes:02d}'",
            "absolute_longitude": round(abs_lon, 4),
        })

    moon_illum, moon_phase = get_moon_phase(observer)

    result = {
        "date": date_str,
        "timestamp_utc": now_utc.isoformat(),
        "positions": positions,
        "moon_phase": {
            "illumination": round(moon_illum, 1),
            "phase_name": moon_phase,
        },
    }

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{date_str}.json"
    out_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
