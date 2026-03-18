#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

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

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_zodiac(ra_rad: float, dec_rad: float, body, observer) -> tuple[str, float, float]:
    """Convert ecliptic longitude to zodiac sign + degree."""
    ecl = ephem.Ecliptic(body)
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return ZODIAC_SIGNS[sign_index], round(degree_in_sign, 2), round(lon_deg, 4)


def get_moon_phase(observer) -> dict:
    """Return moon illumination and phase info."""
    moon = ephem.Moon(observer)
    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new) - float(prev_new)
    days_since_new = float(observer.date) - float(prev_new)
    phase_pct = (days_since_new / cycle_length) * 100

    if phase_pct < 1.5:
        phase_name = "New Moon"
    elif phase_pct < 25:
        phase_name = "Waxing Crescent"
    elif phase_pct < 26.5:
        phase_name = "First Quarter"
    elif phase_pct < 50:
        phase_name = "Waxing Gibbous"
    elif phase_pct < 51.5:
        phase_name = "Full Moon"
    elif phase_pct < 75:
        phase_name = "Waning Gibbous"
    elif phase_pct < 76.5:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    return {
        "phase_name": phase_name,
        "illumination_pct": round(moon.phase, 2),
        "days_since_new": round(days_since_new, 1),
        "next_new_moon": str(ephem.Date(next_new)),
    }


def is_retrograde(body, observer) -> bool:
    """Check if a planet is retrograde by comparing positions 1 day apart."""
    if isinstance(body, (ephem.Sun, ephem.Moon)):
        return False
    ecl_now = ephem.Ecliptic(body)
    lon_now = float(ecl_now.lon)

    saved_date = observer.date
    observer.date = observer.date + 1
    body.compute(observer)
    ecl_next = ephem.Ecliptic(body)
    lon_next = float(ecl_next.lon)
    observer.date = saved_date
    body.compute(observer)

    diff = lon_next - lon_now
    if diff > math.pi:
        diff -= 2 * math.pi
    elif diff < -math.pi:
        diff += 2 * math.pi
    return diff < 0


def fetch_transits(date_str: str | None = None) -> dict:
    """Calculate planetary positions for the given date (default: today UTC)."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.date = f"{date_str} 12:00:00"
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0

    positions = []
    for name, planet_class in PLANETS:
        body = planet_class(observer)
        sign, degree, abs_lon = ecliptic_to_zodiac(body.ra, body.dec, body, observer)
        retro = is_retrograde(body, observer)
        positions.append({
            "planet": name,
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_longitude": abs_lon,
            "retrograde": retro,
        })

    moon_phase = get_moon_phase(observer)

    result = {
        "date": date_str,
        "calculated_at_utc": "12:00:00",
        "positions": positions,
        "moon_phase": moon_phase,
    }
    return result


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    result = fetch_transits(date_str)
    date = result["date"]

    out_path = Path(__file__).parent.parent / "data" / f"transits_{date}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
