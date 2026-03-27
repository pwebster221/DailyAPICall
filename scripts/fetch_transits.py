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


def ecliptic_to_zodiac(ra_rad: float, dec_rad: float, body, observer) -> dict:
    """Convert body position to ecliptic longitude, then zodiac sign + degree."""
    ecl = ephem.Ecliptic(body)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "absolute_degree": round(lon_deg, 2),
        "formatted": f"{degree_in_sign:.0f}°{ZODIAC_SIGNS[sign_index][:3]}",
    }


def get_moon_phase(observer) -> dict:
    """Calculate moon phase details."""
    moon = ephem.Moon(observer)
    phase_pct = moon.phase
    sun = ephem.Sun(observer)

    moon_ecl = ephem.Ecliptic(moon)
    sun_ecl = ephem.Ecliptic(sun)
    elongation = math.degrees(float(moon_ecl.lon) - float(sun_ecl.lon)) % 360

    if elongation < 45:
        phase_name = "New Moon" if elongation < 10 else "Waxing Crescent"
    elif elongation < 90:
        phase_name = "Waxing Crescent"
    elif elongation < 135:
        phase_name = "First Quarter" if elongation < 100 else "Waxing Gibbous"
    elif elongation < 180:
        phase_name = "Waxing Gibbous"
    elif elongation < 225:
        phase_name = "Full Moon" if elongation < 190 else "Waning Gibbous"
    elif elongation < 270:
        phase_name = "Waning Gibbous"
    elif elongation < 315:
        phase_name = "Last Quarter" if elongation < 280 else "Waning Crescent"
    else:
        phase_name = "Waning Crescent"

    lunar_day = elongation / (360 / 29.53)

    return {
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "elongation": round(elongation, 1),
        "lunar_day": round(lunar_day, 1),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    """Fetch planetary positions for the given date (YYYY-MM-DD) or today."""
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

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls(observer)
        pos = ecliptic_to_zodiac(body.ra, body.dec, body, observer)
        positions[name] = pos

    moon_phase = get_moon_phase(observer)

    result = {
        "date": dt.strftime("%Y-%m-%d"),
        "computed_utc": dt.isoformat(),
        "planets": positions,
        "moon_phase": moon_phase,
    }
    return result


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_str)

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"
    out_path.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
