#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def ecliptic_to_sign(ecl_lon_rad: float) -> tuple[str, float]:
    """Convert ecliptic longitude (radians) to zodiac sign + degree within sign."""
    import math
    deg = math.degrees(ecl_lon_rad) % 360
    sign_idx = int(deg // 30)
    degree_in_sign = deg % 30
    return SIGNS[sign_idx], round(degree_in_sign, 2)


def is_retrograde(body, date) -> bool:
    """Check if a planet is retrograde by comparing positions 1 day apart."""
    import math
    obs1 = ephem.Observer()
    obs1.date = date - 0.5
    body.compute(obs1)
    ecl1 = ephem.Ecliptic(body)
    lon1 = math.degrees(ecl1.lon) % 360

    obs2 = ephem.Observer()
    obs2.date = date + 0.5
    body.compute(obs2)
    ecl2 = ephem.Ecliptic(body)
    lon2 = math.degrees(ecl2.lon) % 360

    diff = lon2 - lon1
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360

    return diff < 0


def fetch_transits(date_str: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    if date_str:
        now = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    obs = ephem.Observer()
    obs.date = ephem.Date(now)

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(obs)
        ecl = ephem.Ecliptic(body)
        sign, degree = ecliptic_to_sign(ecl.lon)

        import math
        abs_degree = round(math.degrees(ecl.lon) % 360, 2)

        entry = {
            "sign": sign,
            "degree_in_sign": degree,
            "absolute_degree": abs_degree,
        }

        if name not in ("Sun", "Moon"):
            entry["retrograde"] = is_retrograde(body, obs.date)

        positions[name] = entry

    moon_phase = obs.date - ephem.previous_new_moon(obs.date)
    cycle_length = ephem.next_new_moon(obs.date) - ephem.previous_new_moon(obs.date)
    illumination = round(body.phase if hasattr(body, 'phase') else 0, 1)

    moon_body = ephem.Moon()
    moon_body.compute(obs)
    illumination = round(moon_body.phase, 1)

    phase_pct = (moon_phase / cycle_length) * 100
    if phase_pct < 3:
        phase_name = "New Moon"
    elif phase_pct < 25:
        phase_name = "Waxing Crescent"
    elif phase_pct < 28:
        phase_name = "First Quarter"
    elif phase_pct < 50:
        phase_name = "Waxing Gibbous"
    elif phase_pct < 53:
        phase_name = "Full Moon"
    elif phase_pct < 75:
        phase_name = "Waning Gibbous"
    elif phase_pct < 78:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    result = {
        "date": now.strftime("%Y-%m-%d"),
        "computed_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planets": positions,
        "moon_phase": {
            "name": phase_name,
            "illumination_pct": illumination,
            "days_since_new": round(moon_phase, 1),
        },
    }
    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(json.dumps(data, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
