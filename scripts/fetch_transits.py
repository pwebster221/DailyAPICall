#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import os
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


def ecliptic_to_sign(ecl_lon_rad):
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    deg = math.degrees(ecl_lon_rad) % 360
    sign_idx = int(deg // 30)
    sign_deg = deg % 30
    return SIGNS[sign_idx], round(sign_deg, 4), round(deg, 4)


def fetch_transits(date_str=None):
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    obs = ephem.Observer()
    obs.lat = "0"
    obs.lon = "0"
    obs.elevation = 0
    obs.pressure = 0
    obs.date = ephem.Date(now_utc)

    results = {"date": now_utc.strftime("%Y-%m-%d"), "utc_time": now_utc.strftime("%Y-%m-%d %H:%M UTC"), "planets": {}}

    for name, body_cls in PLANETS:
        body = body_cls()
        body.compute(obs)
        ecl = ephem.Ecliptic(body, epoch=obs.date)
        sign, sign_deg, abs_deg = ecliptic_to_sign(ecl.lon)
        results["planets"][name] = {
            "sign": sign,
            "degree_in_sign": round(sign_deg, 2),
            "absolute_degree": round(abs_deg, 2),
            "formatted": f"{sign} {int(sign_deg)}°{int((sign_deg % 1) * 60):02d}'",
        }

    moon = ephem.Moon()
    moon.compute(obs)
    results["moon_phase"] = {
        "illumination": round(moon.phase, 1),
        "phase_name": _moon_phase_name(obs.date),
    }

    return results


def _moon_phase_name(obs_date):
    prev_new = ephem.previous_new_moon(obs_date)
    next_new = ephem.next_new_moon(obs_date)
    cycle_length = next_new - prev_new
    days_since = obs_date - prev_new
    fraction = days_since / cycle_length

    if fraction < 0.0625:
        return "New Moon"
    elif fraction < 0.25:
        return "Waxing Crescent"
    elif fraction < 0.3125:
        return "First Quarter"
    elif fraction < 0.5:
        return "Waxing Gibbous"
    elif fraction < 0.5625:
        return "Full Moon"
    elif fraction < 0.75:
        return "Waning Gibbous"
    elif fraction < 0.8125:
        return "Last Quarter"
    else:
        return "Waning Crescent"


if __name__ == "__main__":
    data = fetch_transits()
    date_str = data["date"]
    os.makedirs("data", exist_ok=True)
    out_path = f"data/transits_{date_str}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")
