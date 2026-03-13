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

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def ecliptic_to_sign(lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign and degree within sign."""
    lon_deg = math.degrees(lon_rad) % 360
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_index], round(degree_in_sign, 2)


def fetch_transits(date_str: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    if date_str:
        now = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=12)
    else:
        date_str = now.strftime("%Y-%m-%d")
        now = now.replace(hour=12, minute=0, second=0, microsecond=0)

    observer = ephem.Observer()
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")
    observer.pressure = 0
    observer.epoch = ephem.J2000

    positions = {}
    for name, body_cls in PLANETS:
        body = body_cls()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)
        positions[name] = {
            "sign": sign,
            "degree": degree,
            "absolute_degree": round(math.degrees(float(ecl.lon)) % 360, 2),
            "retrograde": getattr(body, "earth_distance", None) is not None
            and hasattr(body, "ra")
            and name not in ("Sun", "Moon"),
        }

    if name not in ("Sun", "Moon"):
        for pname in list(positions.keys()):
            if pname in ("Sun", "Moon"):
                continue
            body_cls_lookup = dict(PLANETS)
            body = body_cls_lookup[pname]()
            body.compute(observer)
            positions[pname]["retrograde"] = body.elong < 0 if hasattr(body, "elong") else False

    for pname in list(positions.keys()):
        if pname in ("Sun", "Moon"):
            positions[pname]["retrograde"] = False
            continue
        body_cls_lookup = dict(PLANETS)
        body = body_cls_lookup[pname]()

        observer_before = ephem.Observer()
        observer_before.date = ephem.Date(observer.date - 1)
        observer_before.pressure = 0
        body_before = body_cls_lookup[pname]()
        body_before.compute(observer_before)
        ecl_before = ephem.Ecliptic(body_before)

        body.compute(observer)
        ecl_now = ephem.Ecliptic(body)

        lon_now = math.degrees(float(ecl_now.lon)) % 360
        lon_before = math.degrees(float(ecl_before.lon)) % 360

        diff = lon_now - lon_before
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        positions[pname]["retrograde"] = diff < 0

    moon_phase = observer.date
    prev_new = ephem.previous_new_moon(moon_phase)
    next_new = ephem.next_new_moon(moon_phase)
    cycle_length = float(next_new) - float(prev_new)
    days_into_cycle = float(moon_phase) - float(prev_new)
    phase_pct = round((days_into_cycle / cycle_length) * 100, 1)

    if phase_pct < 3.4:
        phase_name = "New Moon"
    elif phase_pct < 25:
        phase_name = "Waxing Crescent"
    elif phase_pct < 28.4:
        phase_name = "First Quarter"
    elif phase_pct < 50:
        phase_name = "Waxing Gibbous"
    elif phase_pct < 53.4:
        phase_name = "Full Moon"
    elif phase_pct < 75:
        phase_name = "Waning Gibbous"
    elif phase_pct < 78.4:
        phase_name = "Last Quarter"
    elif phase_pct < 96.6:
        phase_name = "Balsamic"
    else:
        phase_name = "Dark Moon"

    result = {
        "date": date_str,
        "computed_utc": now.isoformat(),
        "positions": positions,
        "moon_phase": {"name": phase_name, "percent_of_cycle": phase_pct},
    }

    out_path = Path(__file__).resolve().parent.parent / "data" / f"transits_{date_str}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_transits(date_arg)
