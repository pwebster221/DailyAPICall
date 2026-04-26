#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone

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


def ecliptic_lon_to_zodiac(rad: float) -> tuple[str, float]:
    deg = math.degrees(rad) % 360
    sign_index = int(deg // 30)
    sign_deg = deg % 30
    return ZODIAC_SIGNS[sign_index], sign_deg


def get_moon_phase(observer: ephem.Observer) -> dict:
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)
    moon_lon = float(ephem.Ecliptic(moon, epoch=observer.date).lon)
    sun_lon = float(ephem.Ecliptic(sun, epoch=observer.date).lon)
    elongation = (math.degrees(moon_lon) - math.degrees(sun_lon)) % 360
    cycle_fraction = elongation / 360.0
    illumination = moon.phase

    new_moon = ephem.previous_new_moon(observer.date)
    days_since_new = observer.date - new_moon

    if elongation < 45:
        phase_name = "New Moon" if elongation < 10 else "Waxing Crescent"
    elif elongation < 90:
        phase_name = "Waxing Crescent"
    elif elongation < 135:
        phase_name = "First Quarter" if elongation < 100 else "Waxing Gibbous"
    elif elongation < 180:
        phase_name = "Waxing Gibbous"
    elif elongation < 225:
        phase_name = "Full Moon" if elongation < 190 else "Waning Gibbous"
    elif elongation < 270:
        phase_name = "Waning Gibbous"
    elif elongation < 315:
        phase_name = "Last Quarter" if elongation < 280 else "Waning Crescent"
    else:
        phase_name = "Waning Crescent" if elongation < 350 else "New Moon"

    return {
        "phase_name": phase_name,
        "illumination_pct": round(illumination, 1),
        "cycle_fraction": round(cycle_fraction, 3),
        "elongation_deg": round(elongation, 1),
        "days_since_new_moon": round(days_since_new, 1),
        "day_of_cycle": int(days_since_new) + 1,
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now = datetime.now(timezone.utc) if date_str is None else datetime.strptime(date_str, "%Y-%m-%d").replace(hour=12)
    observer = ephem.Observer()
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")

    planets = {}
    for name, planet_class in PLANETS:
        body = planet_class(observer)
        ecl = ephem.Ecliptic(body, epoch=observer.date)
        lon_deg = math.degrees(float(ecl.lon)) % 360
        sign, sign_deg = ecliptic_lon_to_zodiac(float(ecl.lon))
        deg_int = int(sign_deg)
        min_int = int((sign_deg - deg_int) * 60)
        planets[name] = {
            "sign": sign,
            "degree": round(sign_deg, 2),
            "absolute_degree": round(lon_deg, 2),
            "formatted": f"{deg_int}°{min_int:02d}' {sign}",
        }

    moon_phase = get_moon_phase(observer)

    result = {
        "date": now.strftime("%Y-%m-%d"),
        "time_utc": now.strftime("%H:%M UTC"),
        "planets": planets,
        "moon_phase": moon_phase,
    }
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    date_str = data["date"]
    output_path = f"data/transits_{date_str}.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Transit data saved to {output_path}")
    print(json.dumps(data, indent=2))
