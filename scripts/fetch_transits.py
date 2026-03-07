#!/usr/bin/env python3
"""Fetch geocentric planetary positions for today using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
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


def ecliptic_to_zodiac(ra_rad, dec_rad, date):
    """Convert RA/Dec to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    whole_deg = int(degree_in_sign)
    minutes = int((degree_in_sign - whole_deg) * 60)
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "formatted": f"{whole_deg}°{minutes:02d}' {ZODIAC_SIGNS[sign_index]}",
        "longitude": round(lon_deg, 4),
    }


def retrograde_status(body):
    """Check if a planet appears to be in retrograde (negative daily motion)."""
    if hasattr(body, "earth_distance"):
        try:
            elong = float(body.elong)
            return getattr(body, "_ra_rate", None)
        except Exception:
            pass
    return None


def fetch_transits(date_str=None):
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now_utc = now_utc.replace(hour=12)

    obs = ephem.Observer()
    obs.lat = "0"
    obs.lon = "0"
    obs.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")

    results = {"date": now_utc.strftime("%Y-%m-%d"), "planets": {}}

    for name, planet_cls in PLANETS.items():
        body = planet_cls()
        body.compute(obs)
        pos = ecliptic_to_zodiac(body.ra, body.dec, obs.date)
        results["planets"][name] = pos

    return results


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    date_str = data["date"]

    output_path = f"data/transits_{date_str}.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
