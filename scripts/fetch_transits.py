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

SIGN_GLYPHS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}


def ecliptic_longitude_to_sign(lon_rad: float) -> dict:
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    lon_deg = math.degrees(lon_rad) % 360
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg - (sign_index * 30)
    sign = SIGNS[sign_index]
    deg = int(degree_in_sign)
    minute = int((degree_in_sign - deg) * 60)
    return {
        "sign": sign,
        "glyph": SIGN_GLYPHS[sign],
        "degree": deg,
        "minute": minute,
        "absolute_degree": round(lon_deg, 4),
        "formatted": f"{deg}°{minute:02d}' {sign}",
    }


def get_moon_phase(observer: ephem.Observer) -> dict:
    """Calculate moon phase details."""
    moon = ephem.Moon(observer)
    phase_pct = moon.phase
    sun = ephem.Sun(observer)
    moon_lon = math.degrees(float(ephem.Ecliptic(moon).lon)) % 360
    sun_lon = math.degrees(float(ephem.Ecliptic(sun).lon)) % 360
    elongation = (moon_lon - sun_lon) % 360
    lunar_day = elongation / (360 / 29.53)

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

    return {
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "lunar_day": round(lunar_day, 1),
        "elongation": round(elongation, 2),
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
    observer.pressure = 0

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls(observer)
        ecl = ephem.Ecliptic(body)
        positions[name] = ecliptic_longitude_to_sign(float(ecl.lon))

    moon_phase = get_moon_phase(observer)

    result = {
        "date": dt.strftime("%Y-%m-%d"),
        "computed_utc": dt.isoformat(),
        "planets": positions,
        "moon_phase": moon_phase,
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"
    out_path.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
