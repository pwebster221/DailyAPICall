#!/usr/bin/env python3
"""Fetch geocentric planetary positions for today using PyEphem."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

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


def ecliptic_lon_to_sign(lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    deg = math.degrees(lon_rad) % 360
    idx = int(deg // 30)
    sign_deg = deg - idx * 30
    return SIGNS[idx], round(sign_deg, 4)


def fetch(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now_utc = now_utc.replace(hour=12)

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.elevation = 0
    observer.date = ephem.Date(now_utc)

    positions = {}
    for name, cls in PLANETS.items():
        body = cls()
        body.compute(observer.date, epoch=observer.date)
        sign, deg = ecliptic_lon_to_sign(body.hlong if hasattr(body, "hlong") and name not in ("Sun", "Moon") else body.ra)

        ecl = ephem.Ecliptic(body, epoch=observer.date)
        sign, deg = ecliptic_lon_to_sign(float(ecl.lon))
        deg_int = int(deg)
        minutes = round((deg - deg_int) * 60, 1)
        positions[name] = {
            "sign": sign,
            "degree": deg,
            "formatted": f"{deg_int}°{minutes:04.1f}' {sign}",
            "absolute_degree": round((SIGNS.index(sign) * 30) + deg, 4),
        }

    moon_phase_pct = observer.date - ephem.previous_new_moon(observer.date)
    cycle_length = ephem.next_new_moon(observer.date) - ephem.previous_new_moon(observer.date)
    cycle_fraction = moon_phase_pct / cycle_length
    illumination = round(body_illum(observer.date), 1)

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "timestamp_utc": now_utc.isoformat(),
        "positions": positions,
        "moon_phase": {
            "cycle_day": round(moon_phase_pct, 1),
            "cycle_fraction": round(cycle_fraction, 3),
            "illumination_pct": illumination,
            "phase_name": phase_name(cycle_fraction),
        },
    }
    return result


def body_illum(date) -> float:
    m = ephem.Moon()
    m.compute(date)
    return m.phase


def phase_name(frac: float) -> str:
    if frac < 0.0625:
        return "New Moon"
    elif frac < 0.1875:
        return "Waxing Crescent"
    elif frac < 0.3125:
        return "First Quarter"
    elif frac < 0.4375:
        return "Waxing Gibbous"
    elif frac < 0.5625:
        return "Full Moon"
    elif frac < 0.6875:
        return "Waning Gibbous"
    elif frac < 0.8125:
        return "Last Quarter"
    elif frac < 0.9375:
        return "Waning Crescent"
    else:
        return "New Moon"


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch(date_arg)
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(json.dumps(data, indent=2))
