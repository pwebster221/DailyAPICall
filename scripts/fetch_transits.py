#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import sys
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

def ecliptic_lon_to_sign(lon_rad):
    """Convert ecliptic longitude (radians) to sign + degree."""
    lon_deg = math.degrees(lon_rad) % 360
    sign_idx = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_idx], round(degree_in_sign, 4), round(lon_deg, 4)


def fetch_transits(date_str=None):
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )
    d = ephem.Date(now_utc)

    results = {"date": now_utc.strftime("%Y-%m-%d"), "time_utc": "12:00:00", "planets": {}}

    for name, cls in PLANETS.items():
        body = cls()
        body.compute(d)
        ecl = ephem.Ecliptic(body)
        sign, deg_in_sign, abs_deg = ecliptic_lon_to_sign(ecl.lon)
        results["planets"][name] = {
            "sign": sign,
            "degree_in_sign": deg_in_sign,
            "absolute_degree": abs_deg,
            "formatted": f"{deg_in_sign:.2f}° {sign}",
        }

    moon_phase = ephem.Moon(d)
    results["moon_phase"] = round(moon_phase.phase, 1)

    sun_lon = results["planets"]["Sun"]["absolute_degree"]
    moon_lon = results["planets"]["Moon"]["absolute_degree"]
    elongation = (moon_lon - sun_lon) % 360
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
    results["moon_phase_name"] = phase_name
    results["moon_illumination"] = results["moon_phase"]

    return results


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    outpath = f"data/transits_{data['date']}.json"
    with open(outpath, "w") as f:
        json.dump(data, f, indent=2)
    print(json.dumps(data, indent=2))
    print(f"\nSaved to {outpath}")
