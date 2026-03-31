#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import ephem

SIGNS = [
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


def ecliptic_to_zodiac(lon_rad: float) -> dict:
    """Convert ecliptic longitude (radians) to zodiac sign, degree, minute."""
    deg = math.degrees(lon_rad) % 360
    sign_idx = int(deg // 30)
    sign_deg = deg - sign_idx * 30
    whole_deg = int(sign_deg)
    minutes = int((sign_deg - whole_deg) * 60)
    return {
        "sign": SIGNS[sign_idx],
        "degree": whole_deg,
        "minute": minutes,
        "absolute_degree": round(deg, 4),
        "formatted": f"{whole_deg}°{minutes:02d}' {SIGNS[sign_idx]}",
    }


def compute_moon_phase(observer: ephem.Observer) -> dict:
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)
    moon_lon = float(ephem.Ecliptic(moon).lon)
    sun_lon = float(ephem.Ecliptic(sun).lon)
    elongation = (math.degrees(moon_lon) - math.degrees(sun_lon)) % 360
    illumination = round(moon.phase, 1)
    lunar_day = round(elongation / (360 / 29.53), 1)

    if elongation < 45:
        phase_name = "New Moon"
    elif elongation < 90:
        phase_name = "Waxing Crescent"
    elif elongation < 135:
        phase_name = "First Quarter"
    elif elongation < 180:
        phase_name = "Waxing Gibbous"
    elif elongation < 225:
        phase_name = "Full Moon"
    elif elongation < 270:
        phase_name = "Waning Gibbous"
    elif elongation < 315:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    return {
        "phase": phase_name,
        "illumination_pct": illumination,
        "elongation": round(elongation, 2),
        "lunar_day": lunar_day,
    }


def main():
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"

    positions = {}
    for name, cls in PLANETS:
        body = cls(observer)
        ecl = ephem.Ecliptic(body)
        zodiac = ecliptic_to_zodiac(float(ecl.lon))
        positions[name] = zodiac

        is_retro = False
        if hasattr(body, "earth_distance"):
            try:
                observer_tomorrow = ephem.Observer()
                observer_tomorrow.date = observer.date + 1
                observer_tomorrow.lat = "0"
                observer_tomorrow.lon = "0"
                body_tomorrow = cls(observer_tomorrow)
                ecl_tomorrow = ephem.Ecliptic(body_tomorrow)
                lon_diff = math.degrees(float(ecl_tomorrow.lon) - float(ecl.lon))
                if lon_diff < -180:
                    lon_diff += 360
                elif lon_diff > 180:
                    lon_diff -= 360
                is_retro = lon_diff < 0
                positions[name]["daily_motion"] = round(lon_diff, 4)
            except Exception:
                pass
        positions[name]["retrograde"] = is_retro

    moon_phase = compute_moon_phase(observer)

    output = {
        "date": date_str,
        "timestamp_utc": now_utc.isoformat(),
        "positions": positions,
        "moon_phase": moon_phase,
    }

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{date_str}.json"
    out_path.write_text(json.dumps(output, indent=2))

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    main()
