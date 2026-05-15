#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem.

Observer: 0°N, 0°E, noon UTC, tropical zodiac.
Output: data/transits_YYYY-MM-DD.json
"""

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

AYANAMSA = 0.0  # tropical


def ecliptic_to_sign(ecl_lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    import math
    deg = math.degrees(ecl_lon_rad) % 360
    sign_idx = int(deg // 30)
    sign_deg = deg % 30
    return SIGNS[sign_idx], round(sign_deg, 2)


def compute_moon_phase(observer: ephem.Observer, date: ephem.Date):
    """Compute lunation phase details."""
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)
    import math
    moon_lon = math.degrees(float(ephem.Ecliptic(moon).lon)) % 360
    sun_lon = math.degrees(float(ephem.Ecliptic(sun).lon)) % 360
    elongation = (moon_lon - sun_lon) % 360
    illumination = round(moon.phase, 1)

    if elongation < 45:
        phase_name = "New Moon" if elongation < 10 else "Waxing Crescent"
    elif elongation < 90:
        phase_name = "Waxing Crescent"
    elif elongation < 135:
        phase_name = "First Quarter" if abs(elongation - 90) < 5 else "Waxing Gibbous"
    elif elongation < 180:
        phase_name = "Waxing Gibbous"
    elif elongation < 225:
        phase_name = "Full Moon" if abs(elongation - 180) < 10 else "Waning Gibbous"
    elif elongation < 270:
        phase_name = "Waning Gibbous" if elongation < 260 else "Last Quarter"
    elif elongation < 315:
        phase_name = "Last Quarter" if abs(elongation - 270) < 5 else "Waning Crescent"
    else:
        phase_name = "Waning Crescent" if elongation < 350 else "Balsamic"

    cycle_fraction = round(elongation / 360, 3)
    day_of_cycle = round(elongation / 360 * 29.53, 1)

    return {
        "phase_name": phase_name,
        "illumination_pct": illumination,
        "elongation_deg": round(elongation, 2),
        "cycle_fraction": cycle_fraction,
        "day_of_cycle": day_of_cycle,
    }


def fetch_transits(date_str: str | None = None) -> dict:
    """Compute planetary positions for a given date (YYYY-MM-DD) or today."""
    import math

    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.elevation = 0
    observer.date = f"{date_str} 12:00:00"

    positions = {}
    for name, planet_cls in PLANETS.items():
        body = planet_cls(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(float(ecl.lon))
        total_deg = round(math.degrees(float(ecl.lon)) % 360, 2)
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "total_ecliptic_longitude": total_deg,
            "formatted": f"{degree:.2f}° {sign}",
        }

    moon_phase = compute_moon_phase(observer, observer.date)

    result = {
        "date": date_str,
        "computation": {
            "method": "PyEphem 4.2.1",
            "observer": "0°N, 0°E",
            "time": "12:00 UTC",
            "zodiac": "tropical",
        },
        "positions": positions,
        "moon_phase": moon_phase,
    }

    out_path = Path(__file__).resolve().parent.parent / "data" / f"transits_{date_str}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
