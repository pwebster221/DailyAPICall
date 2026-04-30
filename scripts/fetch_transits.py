#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
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


def ecliptic_longitude(body, observer):
    """Return ecliptic longitude in degrees (epoch-of-date)."""
    body.compute(observer)
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    return math.degrees(ecl.lon) % 360


def degree_to_sign(deg):
    """Convert ecliptic longitude to zodiac sign + degree within sign."""
    sign_index = int(deg // 30)
    sign_deg = deg % 30
    return ZODIAC_SIGNS[sign_index], sign_deg


def moon_phase_info(observer):
    """Calculate lunar phase details."""
    now = observer.date
    prev_new = ephem.previous_new_moon(now)
    next_new = ephem.next_new_moon(now)
    cycle_length = float(next_new - prev_new)
    days_since_new = float(now - prev_new)
    fraction = days_since_new / cycle_length if cycle_length else 0

    m = ephem.Moon()
    m.compute(observer)
    illumination = m.phase

    if fraction < 0.125:
        phase_name = "New Moon"
    elif fraction < 0.25:
        phase_name = "Waxing Crescent"
    elif fraction < 0.375:
        phase_name = "First Quarter"
    elif fraction < 0.5:
        phase_name = "Waxing Gibbous"
    elif fraction < 0.625:
        phase_name = "Full Moon"
    elif fraction < 0.75:
        phase_name = "Waning Gibbous"
    elif fraction < 0.875:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    day_of_cycle = int(days_since_new) + 1

    return {
        "phase_name": phase_name,
        "illumination_pct": round(illumination, 1),
        "day_of_cycle": day_of_cycle,
        "cycle_fraction": round(fraction, 3),
        "prev_new_moon": str(ephem.Date(prev_new)),
    }


def main():
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"
    observer.pressure = 0

    positions = {}
    for name, cls in PLANETS:
        body = cls()
        lon = ecliptic_longitude(body, observer)
        sign, sign_deg = degree_to_sign(lon)
        positions[name] = {
            "longitude": round(lon, 4),
            "sign": sign,
            "degree_in_sign": round(sign_deg, 2),
            "formatted": f"{int(sign_deg)}°{int((sign_deg % 1) * 60):02d}' {sign}",
        }

    moon_info = moon_phase_info(observer)

    result = {
        "date": date_str,
        "utc_time": now_utc.strftime("%H:%M UTC"),
        "planets": positions,
        "moon_phase": moon_info,
    }

    output_path = Path(__file__).resolve().parent.parent / "data" / f"transits_{date_str}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
