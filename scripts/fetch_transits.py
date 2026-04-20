#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem.

Outputs positions for Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn,
Uranus, Neptune, Pluto as zodiac sign + degree and saves to
data/transits_YYYY-MM-DD.json.
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

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


def ecliptic_lon_to_sign(rad: float) -> tuple[str, float]:
    deg = math.degrees(rad) % 360
    sign_idx = int(deg // 30)
    sign_deg = deg % 30
    return SIGNS[sign_idx], round(sign_deg, 2)


def get_moon_phase(observer: ephem.Observer) -> dict:
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)
    moon_lon = float(ephem.Ecliptic(moon, epoch=observer.date).lon)
    sun_lon = float(ephem.Ecliptic(sun, epoch=observer.date).lon)
    elongation = (math.degrees(moon_lon) - math.degrees(sun_lon)) % 360
    illumination = round(moon.phase, 1)
    cycle_fraction = round(elongation / 360, 3)

    if elongation < 10:
        phase_name = "New Moon"
    elif elongation < 80:
        phase_name = "Waxing Crescent"
    elif elongation < 100:
        phase_name = "First Quarter"
    elif elongation < 170:
        phase_name = "Waxing Gibbous"
    elif elongation < 190:
        phase_name = "Full Moon"
    elif elongation < 260:
        phase_name = "Waning Gibbous"
    elif elongation < 280:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    return {
        "phase": phase_name,
        "illumination_pct": illumination,
        "elongation": round(elongation, 1),
        "cycle_fraction": cycle_fraction,
    }


def main():
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = ephem.Date(now_utc)

    positions = {}
    for name, planet_class in PLANETS:
        body = planet_class(observer)
        ecl = ephem.Ecliptic(body, epoch=observer.date)
        sign, deg = ecliptic_lon_to_sign(float(ecl.lon))
        abs_deg = round(math.degrees(float(ecl.lon)) % 360, 2)
        positions[name] = {
            "sign": sign,
            "degree_in_sign": deg,
            "absolute_degree": abs_deg,
            "formatted": f"{deg:.2f}° {sign}",
        }

    moon_phase = get_moon_phase(observer)

    result = {
        "date": date_str,
        "timestamp_utc": now_utc.isoformat(),
        "planets": positions,
        "moon_phase": moon_phase,
    }

    out_path = Path(__file__).resolve().parent.parent / "data" / f"transits_{date_str}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
