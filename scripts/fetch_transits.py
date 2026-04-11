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

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_zodiac(ra_rad, dec_rad, date):
    """Convert RA/Dec to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=date))
    lon_deg = float(ecl.lon) * 180.0 / 3.141592653589793
    sign_index = int(lon_deg / 30)
    degree_in_sign = lon_deg - sign_index * 30
    return {
        "sign": ZODIAC_SIGNS[sign_index % 12],
        "degree": round(degree_in_sign, 2),
        "absolute_degree": round(lon_deg, 2),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, tzinfo=timezone.utc
        )

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        pos = ecliptic_to_zodiac(body.ra, body.dec, observer.date)
        positions[name] = pos

    moon = ephem.Moon()
    moon.compute(observer)
    phase_pct = round(moon.phase, 1)

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    next_full = ephem.next_full_moon(observer.date)
    next_first_q = ephem.next_first_quarter_moon(observer.date)
    next_last_q = ephem.next_last_quarter_moon(observer.date)

    cycle_length = float(next_new) - float(prev_new)
    days_since_new = float(observer.date) - float(prev_new)
    if days_since_new < cycle_length * 0.25:
        lunar_phase_name = "Waxing Crescent"
    elif days_since_new < cycle_length * 0.5:
        lunar_phase_name = "Waxing Gibbous"
    elif days_since_new < cycle_length * 0.75:
        lunar_phase_name = "Waning Gibbous"
    else:
        lunar_phase_name = "Waning Crescent"

    if phase_pct > 98:
        lunar_phase_name = "Full Moon"
    elif phase_pct < 2:
        lunar_phase_name = "New Moon"
    elif abs(phase_pct - 50) < 3 and days_since_new < cycle_length * 0.5:
        lunar_phase_name = "First Quarter"
    elif abs(phase_pct - 50) < 3 and days_since_new >= cycle_length * 0.5:
        lunar_phase_name = "Last Quarter"

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_at_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "planets": positions,
        "moon_phase": {
            "illumination_pct": phase_pct,
            "phase_name": lunar_phase_name,
        },
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    date_str = data["date"]

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"transits_{date_str}.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
