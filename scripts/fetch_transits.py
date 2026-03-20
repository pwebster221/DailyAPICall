#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

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


def ecliptic_lon(body: ephem.Body, observer_date: ephem.Date) -> float:
    """Return geocentric ecliptic longitude in degrees."""
    body.compute(observer_date)
    ecl = ephem.Ecliptic(body)
    return math.degrees(float(ecl.lon))


def lon_to_sign_degree(lon: float) -> dict:
    idx = int(lon // 30) % 12
    degree = lon % 30
    return {
        "sign": ZODIAC_SIGNS[idx],
        "degree": round(degree, 2),
        "absolute_degree": round(lon, 2),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    if date_str:
        now = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = now.replace(hour=12)

    obs_date = ephem.Date(now)
    positions = {}
    for name, cls in PLANETS.items():
        body = cls()
        lon = ecliptic_lon(body, obs_date)
        info = lon_to_sign_degree(lon)
        body.compute(obs_date)
        info["ra"] = str(body.ra)
        info["dec"] = str(body.dec)
        positions[name] = info

    moon = ephem.Moon()
    moon.compute(obs_date)

    result = {
        "date": now.strftime("%Y-%m-%d"),
        "computed_utc": now.isoformat(),
        "positions": positions,
        "moon_phase": round(moon.phase, 2),
    }
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"transits_{data['date']}.json"
    out_file.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))
