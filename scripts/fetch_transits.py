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

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_sign(ecliptic_lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree."""
    import math
    deg = math.degrees(ecliptic_lon_rad) % 360
    sign_index = int(deg // 30)
    sign_degree = deg % 30
    return SIGNS[sign_index], round(sign_degree, 2)


def get_moon_phase(observer: ephem.Observer) -> dict:
    """Return moon phase info."""
    moon = ephem.Moon(observer)
    phase_pct = moon.phase
    prev_new = ephem.previous_new_moon(observer.date)
    day_of_cycle = observer.date - prev_new
    next_full = ephem.next_full_moon(observer.date)
    if phase_pct < 1:
        phase_name = "New Moon"
    elif day_of_cycle < 7.38:
        phase_name = "Waxing Crescent"
    elif day_of_cycle < 10.5:
        phase_name = "First Quarter"
    elif day_of_cycle < 14.5:
        phase_name = "Waxing Gibbous"
    elif phase_pct > 98:
        phase_name = "Full Moon"
    elif day_of_cycle < 22:
        phase_name = "Waning Gibbous"
    elif day_of_cycle < 25.5:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"
    return {
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "day_of_cycle": round(day_of_cycle, 1),
        "next_full_moon": str(ephem.Date(next_full)),
    }


def fetch_transits(date_str: str | None = None) -> dict:
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    observer = ephem.Observer()
    observer.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"

    positions = {}
    for name, body_cls in PLANETS.items():
        body = body_cls(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        positions[name] = {
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_degree": round(float(ecl.lon) * 180 / 3.14159265358979, 2),
        }

    moon_phase = get_moon_phase(observer)

    result = {
        "date": now_utc.strftime("%Y-%m-%d"),
        "computed_utc": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "planets": positions,
        "moon_phase": moon_phase,
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    outdir = Path(__file__).resolve().parent.parent / "data"
    outdir.mkdir(exist_ok=True)
    outfile = outdir / f"transits_{data['date']}.json"
    outfile.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
