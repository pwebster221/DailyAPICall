#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import ephem
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
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


def ecliptic_to_zodiac(ra_rad, dec_rad, body, observer):
    """Convert a body's position to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(body)
    lon_deg = float(ecl.lon) * 180.0 / ephem.pi
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
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

    result = {"date": now_utc.strftime("%Y-%m-%d"), "planets": {}}

    for name, planet_class in PLANETS.items():
        body = planet_class()
        body.compute(observer)
        pos = ecliptic_to_zodiac(body.ra, body.dec, body, observer)

        retrograde = False
        if hasattr(body, "earth_distance"):
            try:
                observer_tomorrow = ephem.Observer()
                observer_tomorrow.lat = "0"
                observer_tomorrow.lon = "0"
                observer_tomorrow.date = observer.date + 1
                body_tomorrow = planet_class()
                body_tomorrow.compute(observer_tomorrow)
                ecl_today = ephem.Ecliptic(body)
                ecl_tomorrow = ephem.Ecliptic(body_tomorrow)
                if float(ecl_tomorrow.lon) < float(ecl_today.lon):
                    retrograde = True
            except Exception:
                pass

        pos["retrograde"] = retrograde
        result["planets"][name] = pos

    moon_phase = observer.date - ephem.previous_new_moon(observer.date)
    result["moon_phase_days"] = round(float(moon_phase), 1)
    moon_body = ephem.Moon()
    moon_body.compute(observer)
    result["moon_illumination"] = round(moon_body.phase, 1)

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
