#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import os
from datetime import datetime, timezone

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


def ecliptic_to_sign(ra_rad, dec_rad, body, observer):
    """Convert equatorial coordinates to ecliptic longitude, return sign + degree."""
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg / 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], degree_in_sign, lon_deg


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = ephem.Date(now)
    observer.pressure = 0

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        sign, degree, abs_lon = ecliptic_to_sign(body.ra, body.dec, body, observer)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_longitude": round(abs_lon, 2),
            "formatted": f"{degree:.0f}°{sign[:3]} ({sign} {degree:.2f}°)",
        }

    moon_phase = observer.date - ephem.previous_new_moon(observer.date)
    cycle_length = ephem.next_new_moon(observer.date) - ephem.previous_new_moon(observer.date)
    illumination = body._mag if hasattr(body, '_mag') else None

    m = ephem.Moon()
    m.compute(observer)
    moon_phase_pct = m.phase

    output = {
        "date": date_str,
        "timestamp_utc": now.isoformat(),
        "planets": positions,
        "moon_phase": {
            "days_since_new": round(float(moon_phase), 2),
            "cycle_fraction": round(float(moon_phase) / float(cycle_length), 3),
            "illumination_pct": round(moon_phase_pct, 1),
        },
    }

    os.makedirs("data", exist_ok=True)
    outpath = f"data/transits_{date_str}.json"
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    main()
