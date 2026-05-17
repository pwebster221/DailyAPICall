#!/usr/bin/env python3
"""Fetch geocentric planetary positions for a given date using PyEphem.

Observer: 0°N, 0°E, noon UTC — standardised for tropical zodiac output.
Output: data/transits_YYYY-MM-DD.json
"""

import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

import ephem

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
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


def ecliptic_to_zodiac(ra_rad, dec_rad, observer_date):
    """Convert RA/Dec to ecliptic longitude, then to sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=observer_date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], degree_in_sign, lon_deg


def get_moon_phase(obs):
    """Return moon illumination %, phase name, and cycle day."""
    m = ephem.Moon(obs)
    illum = m.phase

    prev_new = ephem.previous_new_moon(obs.date)
    next_new = ephem.next_new_moon(obs.date)
    cycle_length = float(next_new) - float(prev_new)
    day_in_cycle = float(obs.date) - float(prev_new)
    fraction = day_in_cycle / cycle_length if cycle_length else 0

    if fraction < 0.0625:
        phase = "New Moon"
    elif fraction < 0.1875:
        phase = "Waxing Crescent"
    elif fraction < 0.3125:
        phase = "First Quarter"
    elif fraction < 0.4375:
        phase = "Waxing Gibbous"
    elif fraction < 0.5625:
        phase = "Full Moon"
    elif fraction < 0.6875:
        phase = "Waning Gibbous"
    elif fraction < 0.8125:
        phase = "Last Quarter"
    elif fraction < 0.9375:
        phase = "Waning Crescent"
    else:
        phase = "Balsamic"

    return illum, phase, int(day_in_cycle) + 1, fraction


def compute_transits(target_date: date) -> dict:
    obs = ephem.Observer()
    obs.lat = "0"
    obs.lon = "0"
    obs.elevation = 0
    obs.date = ephem.Date(datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0))

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls(obs)
        sign, deg, abs_lon = ecliptic_to_zodiac(body.ra, body.dec, obs.date)
        positions[name] = {
            "sign": sign,
            "degree": round(deg, 2),
            "absolute_longitude": round(abs_lon, 2),
            "formatted": f"{deg:.0f}°{deg % 1 * 60:.0f}' {sign}",
        }

    illum, phase, cycle_day, fraction = get_moon_phase(obs)
    moon_phase = {
        "illumination_pct": round(illum, 1),
        "phase": phase,
        "cycle_day": cycle_day,
        "cycle_fraction": round(fraction, 3),
    }

    return {
        "date": target_date.isoformat(),
        "observer": "0N 0E, noon UTC",
        "system": "tropical (PyEphem ecliptic)",
        "planets": positions,
        "moon_phase": moon_phase,
    }


def main():
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])
    else:
        target = date.today()

    data = compute_transits(target)

    out_path = Path(__file__).resolve().parent.parent / "data" / f"transits_{target.isoformat()}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
