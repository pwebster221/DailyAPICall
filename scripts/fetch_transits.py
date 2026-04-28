#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def ecliptic_longitude_to_sign(lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree within sign."""
    lon_deg = math.degrees(lon_rad) % 360
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], degree_in_sign


def moon_phase_info(observer_date):
    """Calculate lunar phase details."""
    prev_new = ephem.previous_new_moon(observer_date)
    next_new = ephem.next_new_moon(observer_date)
    cycle_length = float(next_new) - float(prev_new)
    days_since_new = float(observer_date) - float(prev_new)
    fraction = days_since_new / cycle_length if cycle_length else 0
    day_in_cycle = int(days_since_new) + 1

    m = ephem.Moon()
    m.compute(observer_date)
    illumination = m.phase

    if fraction < 0.125:
        phase_name = "New Moon"
    elif fraction < 0.25:
        phase_name = "Waxing Crescent"
    elif fraction < 0.375:
        phase_name = "First Quarter"
    elif fraction < 0.5:
        phase_name = "Waxing Gibbous"
    elif fraction < 0.625:
        phase_name = "Full Moon"
    elif fraction < 0.75:
        phase_name = "Waning Gibbous"
    elif fraction < 0.875:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    return {
        "phase_name": phase_name,
        "day_in_cycle": day_in_cycle,
        "illumination_pct": round(illumination, 1),
        "cycle_fraction": round(fraction, 3),
        "new_moon_date": str(ephem.Date(prev_new)),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    obs = ephem.Observer()
    obs.lat = "0"
    obs.lon = "0"
    obs.date = ephem.Date(now_utc)

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(obs.date, epoch=obs.date)
        ecl = ephem.Ecliptic(body, epoch=obs.date)
        sign, deg = ecliptic_longitude_to_sign(ecl.lon)
        lon_deg = math.degrees(float(ecl.lon)) % 360
        positions[name] = {
            "sign": sign,
            "degree_in_sign": round(deg, 2),
            "longitude": round(lon_deg, 4),
            "formatted": f"{deg:.0f}°{deg % 1 * 60:02.0f}' {sign}",
        }

    moon_info = moon_phase_info(obs.date)
    date_key = now_utc.strftime("%Y-%m-%d")

    result = {
        "date": date_key,
        "utc_time": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planets": positions,
        "moon_phase": moon_info,
    }

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{date_key}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Saved to {out_path}")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
