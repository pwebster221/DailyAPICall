#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
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


def ecliptic_to_sign(ecl_lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign and degree within sign."""
    deg = math.degrees(ecl_lon_rad) % 360
    sign_idx = int(deg // 30)
    degree_in_sign = deg % 30
    return SIGNS[sign_idx], round(degree_in_sign, 2)


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    observer = ephem.Observer()
    observer.date = ephem.Date(now_utc)
    observer.pressure = 0

    positions = {}
    for name, planet_class in PLANETS:
        body = planet_class()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        abs_deg = round(math.degrees(ecl.lon) % 360, 2)

        entry = {
            "sign": sign,
            "degree_in_sign": degree,
            "absolute_degree": abs_deg,
        }

        if name == "Moon":
            entry["phase"] = round(body.phase, 2)
            prev_new = ephem.previous_new_moon(observer.date)
            next_new = ephem.next_new_moon(observer.date)
            cycle_len = float(next_new - prev_new)
            days_since_new = float(observer.date - prev_new)
            entry["days_since_new_moon"] = round(days_since_new, 1)
            entry["cycle_fraction"] = round(days_since_new / cycle_len, 3)
            if days_since_new / cycle_len < 0.0625:
                entry["phase_name"] = "New Moon"
            elif days_since_new / cycle_len < 0.1875:
                entry["phase_name"] = "Waxing Crescent"
            elif days_since_new / cycle_len < 0.3125:
                entry["phase_name"] = "First Quarter"
            elif days_since_new / cycle_len < 0.4375:
                entry["phase_name"] = "Waxing Gibbous"
            elif days_since_new / cycle_len < 0.5625:
                entry["phase_name"] = "Full Moon"
            elif days_since_new / cycle_len < 0.6875:
                entry["phase_name"] = "Waning Gibbous"
            elif days_since_new / cycle_len < 0.8125:
                entry["phase_name"] = "Last Quarter"
            elif days_since_new / cycle_len < 0.9375:
                entry["phase_name"] = "Balsamic"
            else:
                entry["phase_name"] = "Dark Moon"

        positions[name] = entry

    return {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_utc": now_utc.isoformat(),
        "planets": positions,
    }


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(json.dumps(data, indent=2))
