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


def ecliptic_to_sign(ra_rad, dec_rad, body, observer):
    """Convert equatorial coords to ecliptic longitude, return (sign, degree_in_sign, total_degree)."""
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    lon_deg = float(ecl.lon) * 180.0 / 3.141592653589793
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg - sign_index * 30
    return SIGNS[sign_index], degree_in_sign, lon_deg


def fetch_transits(date_str=None):
    now_utc = datetime.now(timezone.utc)
    if date_str:
        now_utc = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=14)
    
    obs = ephem.Observer()
    obs.date = now_utc.strftime("%Y/%m/%d %H:%M:%S")
    obs.lat = "0"
    obs.lon = "0"
    obs.pressure = 0

    result = {"date": now_utc.strftime("%Y-%m-%d"), "time_utc": obs.date.datetime().isoformat(), "planets": {}}

    for name, cls in PLANETS.items():
        body = cls()
        body.compute(obs)
        sign, deg_in_sign, total_deg = ecliptic_to_sign(body.ra, body.dec, body, obs)
        minutes = (deg_in_sign - int(deg_in_sign)) * 60

        moon_extras = {}
        if name == "Moon":
            moon_extras["phase_pct"] = round(body.phase, 1)
            prev_full = ephem.previous_full_moon(obs.date)
            next_new = ephem.next_new_moon(obs.date)
            prev_new = ephem.previous_new_moon(obs.date)
            if float(obs.date - prev_full) < float(next_new - obs.date):
                moon_extras["phase_name"] = "Waning Gibbous" if body.phase > 50 else "Waning Crescent"
                moon_extras["days_since_full"] = round(float(obs.date - prev_full), 1)
            else:
                moon_extras["phase_name"] = "Waxing Crescent" if body.phase < 50 else "Waxing Gibbous"
                moon_extras["days_since_new"] = round(float(obs.date - prev_new), 1)

        result["planets"][name] = {
            "sign": sign,
            "degree_in_sign": round(deg_in_sign, 2),
            "formatted": f"{int(deg_in_sign)}°{int(minutes):02d}' {sign}",
            "total_ecliptic_longitude": round(total_deg, 4),
            **moon_extras,
        }

    return result


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_transits(date_arg)
    
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"transits_{data['date']}.json"
    out_path.write_text(json.dumps(data, indent=2))
    
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    main()
