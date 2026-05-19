#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem.

Observer: 0°N, 0°E, noon UTC (standardized).
Zodiac: Tropical (computed from ecliptic longitude).
Output: data/transits_YYYY-MM-DD.json
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

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
    sign_index = int(deg // 30)
    degree_in_sign = deg - sign_index * 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc) if date_str is None else datetime.strptime(date_str, "%Y-%m-%d")
    d = ephem.Date(now_utc.strftime("%Y/%m/%d 12:00:00"))

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = d
    observer.pressure = 0

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "longitude": round(math.degrees(ecl.lon) % 360, 4),
            "formatted": f"{degree:.2f}° {sign}",
        }

    moon_phase = observer.date
    prev_new = ephem.previous_new_moon(moon_phase)
    next_new = ephem.next_new_moon(moon_phase)
    cycle_length = next_new - prev_new
    cycle_day = moon_phase - prev_new
    illumination = body.__class__ == ephem.Moon

    moon_body = ephem.Moon()
    moon_body.compute(observer)

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computation": {
            "observer": "0°N, 0°E",
            "time": "12:00 UTC",
            "zodiac": "tropical",
            "engine": f"PyEphem {ephem.__version__}",
        },
        "planets": positions,
        "lunar": {
            "phase_day": round(cycle_day, 1),
            "cycle_fraction": round(cycle_day / cycle_length, 3),
            "illumination_pct": round(moon_body.phase, 1),
        },
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"transits_{data['date']}.json")

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
