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
    """Convert ecliptic longitude (radians) to zodiac sign and degree within sign."""
    deg = math.degrees(ecl_lon_rad) % 360
    sign_index = int(deg // 30)
    degree_in_sign = deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def moon_phase_info(observer: ephem.Observer) -> dict:
    """Calculate Moon illumination and phase name."""
    moon = ephem.Moon(observer)
    illum = moon.phase
    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = next_new - prev_new
    days_since_new = observer.date - prev_new
    cycle_fraction = days_since_new / cycle_length

    if cycle_fraction < 0.125:
        phase_name = "New Moon" if illum < 3 else "Waxing Crescent"
    elif cycle_fraction < 0.25:
        phase_name = "Waxing Crescent"
    elif cycle_fraction < 0.375:
        phase_name = "First Quarter"
    elif cycle_fraction < 0.5:
        phase_name = "Waxing Gibbous"
    elif cycle_fraction < 0.625:
        phase_name = "Full Moon" if illum > 97 else "Waning Gibbous"
    elif cycle_fraction < 0.75:
        phase_name = "Waning Gibbous"
    elif cycle_fraction < 0.875:
        phase_name = "Last Quarter" if abs(illum - 50) < 5 else "Waning Crescent"
    else:
        phase_name = "Waning Crescent" if illum > 3 else "Balsamic"

    return {
        "illumination_pct": round(illum, 1),
        "phase": phase_name,
        "cycle_fraction": round(cycle_fraction, 3),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        target = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=now_utc.hour, minute=now_utc.minute, tzinfo=timezone.utc
        )
    else:
        target = now_utc

    observer = ephem.Observer()
    observer.date = ephem.Date(target)
    observer.lat = "0"
    observer.lon = "0"

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class(observer)
        ecl = ephem.Ecliptic(body, epoch=observer.date)
        sign, degree = ecliptic_to_sign(ecl.lon)
        total_deg = round(math.degrees(ecl.lon) % 360, 2)
        positions[name] = {
            "sign": sign,
            "degree_in_sign": degree,
            "total_ecliptic_degree": total_deg,
            "formatted": f"{degree:.2f}° {sign}",
        }

    moon_info = moon_phase_info(observer)

    element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    element_map = {
        "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
        "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
        "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
        "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
    }
    for p in positions.values():
        element_count[element_map[p["sign"]]] += 1

    result = {
        "date": target.strftime("%Y-%m-%d"),
        "time_utc": target.strftime("%H:%M UTC"),
        "planets": positions,
        "moon_phase": moon_info,
        "element_distribution": element_count,
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    out_path = Path(__file__).parent.parent / "data" / f"transits_{data['date']}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
