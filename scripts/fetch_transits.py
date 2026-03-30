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
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_zodiac(ra_rad: float, dec_rad: float, body, observer) -> tuple[str, float]:
    """Convert ecliptic longitude to zodiac sign and degree within sign."""
    ecl = ephem.Ecliptic(body)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def get_moon_phase(observer) -> dict:
    """Calculate moon phase information."""
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)

    moon_ecl = ephem.Ecliptic(moon)
    sun_ecl = ephem.Ecliptic(sun)
    elongation = math.degrees(float(moon_ecl.lon) - float(sun_ecl.lon)) % 360

    phase_pct = moon.phase

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

    lunar_day = elongation / (360 / 29.53)

    return {
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "lunar_day": round(lunar_day, 1),
        "elongation": round(elongation, 2),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    """Fetch planetary positions for the given date (or today)."""
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )
    else:
        dt = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0)

    observer = ephem.Observer()
    observer.date = dt.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0

    positions = {}
    for name, body_class in PLANETS.items():
        body = body_class(observer)
        ecl = ephem.Ecliptic(body)
        lon_deg = math.degrees(float(ecl.lon))
        sign_index = int(lon_deg // 30)
        degree_in_sign = lon_deg % 30
        positions[name] = {
            "sign": SIGNS[sign_index],
            "degree": round(degree_in_sign, 2),
            "abs_degree": round(lon_deg, 2),
            "retrograde": name not in ("Sun", "Moon") and body.elong < 0
            if name in ("Mercury", "Venus")
            else False,
        }
        if name not in ("Sun", "Moon"):
            try:
                positions[name]["retrograde"] = body.elong < 0 if hasattr(body, 'elong') else False
            except Exception:
                positions[name]["retrograde"] = False

    moon_phase = get_moon_phase(observer)

    result = {
        "date": dt.strftime("%Y-%m-%d"),
        "computed_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planets": positions,
        "moon_phase": moon_phase,
    }
    return result


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_str)

    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"transits_{data['date']}.json"
    output_file.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
