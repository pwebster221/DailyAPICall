#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import os
import sys
from datetime import datetime, timezone

import ephem

ZODIAC_SIGNS = [
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


def ecliptic_lon_to_zodiac(lon_rad: float) -> dict:
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    lon_deg = math.degrees(lon_rad) % 360.0
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg - sign_index * 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "absolute_degree": round(lon_deg, 2),
    }


def compute_moon_phase(observer: ephem.Observer) -> dict:
    """Compute lunar phase details."""
    moon = ephem.Moon(observer)
    phase_pct = moon.phase  # 0-100 illumination

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    cycle_length = float(next_new - prev_new)
    days_since_new = float(observer.date - prev_new)
    cycle_fraction = days_since_new / cycle_length if cycle_length else 0

    if cycle_fraction < 0.0625:
        phase_name = "New Moon"
    elif cycle_fraction < 0.1875:
        phase_name = "Waxing Crescent"
    elif cycle_fraction < 0.3125:
        phase_name = "First Quarter"
    elif cycle_fraction < 0.4375:
        phase_name = "Waxing Gibbous"
    elif cycle_fraction < 0.5625:
        phase_name = "Full Moon"
    elif cycle_fraction < 0.6875:
        phase_name = "Waning Gibbous"
    elif cycle_fraction < 0.8125:
        phase_name = "Last Quarter"
    else:
        phase_name = "Balsamic"

    day_of_cycle = int(days_since_new) + 1

    return {
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "cycle_fraction": round(cycle_fraction, 3),
        "day_of_cycle": day_of_cycle,
        "days_since_new_moon": round(days_since_new, 2),
        "new_moon_date": str(ephem.Date(prev_new)),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    """Calculate geocentric positions for all planets at noon UTC on given date."""
    if date_str is None:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.lat = "0"
    observer.lon = "0"
    observer.elevation = 0
    observer.date = f"{date_str} 12:00:00"

    planets = {}
    for name, cls in PLANETS:
        body = cls(observer)
        ecl = ephem.Ecliptic(body, epoch=observer.date)
        info = ecliptic_lon_to_zodiac(float(ecl.lon))
        info["name"] = name
        planets[name] = info

    moon_phase = compute_moon_phase(observer)

    element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    modality_count = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    element_map = {
        "Aries": "Fire", "Taurus": "Earth", "Gemini": "Air", "Cancer": "Water",
        "Leo": "Fire", "Virgo": "Earth", "Libra": "Air", "Scorpio": "Water",
        "Sagittarius": "Fire", "Capricorn": "Earth", "Aquarius": "Air", "Pisces": "Water",
    }
    modality_map = {
        "Aries": "Cardinal", "Taurus": "Fixed", "Gemini": "Mutable", "Cancer": "Cardinal",
        "Leo": "Fixed", "Virgo": "Mutable", "Libra": "Cardinal", "Scorpio": "Fixed",
        "Sagittarius": "Mutable", "Capricorn": "Cardinal", "Aquarius": "Fixed", "Pisces": "Mutable",
    }
    for p in planets.values():
        element_count[element_map[p["sign"]]] += 1
        modality_count[modality_map[p["sign"]]] += 1

    return {
        "date": date_str,
        "computed_at_utc": f"{date_str}T12:00:00Z",
        "planets": planets,
        "moon_phase": moon_phase,
        "elements": element_count,
        "modalities": modality_count,
    }


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_str)

    os.makedirs("data", exist_ok=True)
    out_path = f"data/transits_{data['date']}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Transit data saved to {out_path}")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
