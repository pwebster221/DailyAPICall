#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
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


def ecliptic_to_sign(lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    import math
    lon_deg = math.degrees(lon_rad)
    if lon_deg < 0:
        lon_deg += 360.0
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )
    date_label = now_utc.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.date = ephem.Date(now_utc)
    observer.pressure = 0

    positions = {}
    for name, planet_cls in PLANETS.items():
        body = planet_cls()
        body.compute(observer.date, epoch=observer.date)
        ecl = ephem.Ecliptic(body, epoch=observer.date)
        sign, degree = ecliptic_to_sign(float(ecl.lon))
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "ecliptic_longitude": round(
                float(ecl.lon) * 180.0 / 3.141592653589793, 4
            ),
        }

    moon = ephem.Moon()
    moon.compute(observer.date)
    moon_phase_pct = round(moon.phase, 1)

    result = {
        "date": date_label,
        "utc_time": now_utc.isoformat(),
        "planets": positions,
        "moon_phase_pct": moon_phase_pct,
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
    return data


if __name__ == "__main__":
    main()
