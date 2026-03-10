#!/usr/bin/env python3
"""Fetch geocentric planetary positions for today using PyEphem."""

import ephem
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def ecliptic_to_zodiac(ra_deg: float) -> tuple[str, float]:
    """Convert ecliptic longitude in degrees to zodiac sign + degree within sign."""
    sign_index = int(ra_deg // 30)
    degree_in_sign = ra_deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    observer = ephem.Observer()
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    observer.pressure = 0  # no atmospheric refraction for astrological positions

    positions = {}
    for name, body_class in PLANETS:
        body = body_class()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        lon_deg = float(ecl.lon) * 180.0 / ephem.pi
        sign, degree = ecliptic_to_zodiac(lon_deg)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_degree": round(lon_deg, 2),
        }

    return {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "positions": positions,
    }


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"
    out_path.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
