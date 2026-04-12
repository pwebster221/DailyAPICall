#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone

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


def ecliptic_to_sign(ra_rad, dec_rad, observer_date):
    """Convert RA/Dec to ecliptic longitude, then to sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=observer_date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], degree_in_sign, lon_deg


def get_moon_phase(observer):
    """Return moon illumination percentage and phase name."""
    moon = ephem.Moon(observer)
    illum = moon.phase
    sun = ephem.Sun(observer)
    sun_ecl = ephem.Ecliptic(ephem.Equatorial(sun.ra, sun.dec, epoch=observer.date))
    moon_ecl = ephem.Ecliptic(ephem.Equatorial(moon.ra, moon.dec, epoch=observer.date))
    elongation = (math.degrees(float(moon_ecl.lon)) - math.degrees(float(sun_ecl.lon))) % 360

    if elongation < 45:
        phase_name = "New Moon"
    elif elongation < 90:
        phase_name = "Waxing Crescent"
    elif elongation < 135:
        phase_name = "First Quarter"
    elif elongation < 180:
        phase_name = "Waxing Gibbous"
    elif elongation < 225:
        phase_name = "Full Moon"
    elif elongation < 270:
        phase_name = "Waning Gibbous"
    elif elongation < 315:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    return illum, phase_name, elongation


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = ephem.Date(now)

    positions = []
    for name, planet_class in PLANETS:
        body = planet_class(observer)
        sign, degree, abs_lon = ecliptic_to_sign(body.ra, body.dec, observer.date)
        positions.append({
            "planet": name,
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_longitude": round(abs_lon, 2),
            "formatted": f"{degree:.0f}°{sign[:3]} ({sign} {degree:.2f}°)",
        })

    illum, phase_name, elongation = get_moon_phase(observer)

    result = {
        "date": date_str,
        "timestamp_utc": now.isoformat(),
        "positions": positions,
        "moon_phase": {
            "illumination": round(illum, 1),
            "phase_name": phase_name,
            "elongation": round(elongation, 2),
        },
    }

    output_path = f"data/transits_{date_str}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
