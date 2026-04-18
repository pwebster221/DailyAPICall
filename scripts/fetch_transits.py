#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

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


def ecliptic_to_sign(ecl_lon_rad: float) -> tuple[str, float]:
    deg = math.degrees(ecl_lon_rad) % 360
    sign_idx = int(deg // 30)
    sign_deg = deg - sign_idx * 30
    return SIGNS[sign_idx], round(sign_deg, 2)


def moon_phase_info(observer: ephem.Observer) -> dict:
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)
    elongation = math.degrees(moon.elong) % 360
    illumination = round(moon.phase, 2)
    cycle_fraction = round(elongation / 360, 3)
    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new - prev_new)
    day_in_cycle = float(observer.date - prev_new)
    if elongation < 45:
        phase_name = "New Moon" if illumination < 3 else "Waxing Crescent"
    elif elongation < 90:
        phase_name = "Waxing Crescent"
    elif elongation < 135:
        phase_name = "First Quarter"
    elif elongation < 180:
        phase_name = "Waxing Gibbous"
    elif elongation < 225:
        phase_name = "Full Moon" if illumination > 97 else "Waning Gibbous"
    elif elongation < 270:
        phase_name = "Waning Gibbous"
    elif elongation < 315:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"
    return {
        "phase_name": phase_name,
        "illumination_pct": illumination,
        "cycle_fraction": cycle_fraction,
        "day_in_cycle": round(day_in_cycle, 2),
        "cycle_length_days": round(cycle_length, 2),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    if date_str:
        target = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=now.hour, minute=now.minute, tzinfo=timezone.utc
        )
    else:
        target = now

    obs = ephem.Observer()
    obs.date = target.strftime("%Y/%m/%d %H:%M:%S")

    positions = {}
    for name, planet_cls in PLANETS.items():
        body = planet_cls(obs)
        ecl = ephem.Ecliptic(body, epoch=obs.date)
        sign, deg = ecliptic_to_sign(ecl.lon)
        abs_deg = round(math.degrees(ecl.lon) % 360, 2)
        positions[name] = {
            "sign": sign,
            "degree_in_sign": deg,
            "absolute_degree": abs_deg,
            "formatted": f"{deg:.2f}° {sign}",
        }

    moon_info = moon_phase_info(obs)

    result = {
        "date": target.strftime("%Y-%m-%d"),
        "time_utc": target.strftime("%H:%M UTC"),
        "positions": positions,
        "moon_phase": moon_info,
    }

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{target.strftime('%Y-%m-%d')}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
