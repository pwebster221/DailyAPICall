#!/usr/bin/env python3
"""Fetch geocentric planetary positions for today using PyEphem."""

import ephem
import json
import math
import sys
from datetime import datetime, timezone

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


def ecliptic_to_zodiac(ra_rad, dec_rad, date):
    """Convert RA/Dec to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_rad, dec_rad, epoch=date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_idx = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return SIGNS[sign_idx], degree_in_sign, lon_deg


def main():
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    if len(sys.argv) > 1:
        date_str = sys.argv[1]
        now_utc = datetime.strptime(date_str, "%Y-%m-%d")

    obs = ephem.Observer()
    obs.date = ephem.Date(date_str + " 12:00:00")

    results = {"date": date_str, "planets": []}

    for name, body_cls in PLANETS:
        body = body_cls()
        body.compute(obs)
        sign, deg, abs_lon = ecliptic_to_zodiac(body.ra, body.dec, obs.date)
        entry = {
            "planet": name,
            "sign": sign,
            "degree": round(deg, 2),
            "absolute_longitude": round(abs_lon, 2),
            "retrograde": body.name != "Sun" and body.name != "Moon" and hasattr(body, "elong") and False,
        }
        if hasattr(body, "hlat"):
            try:
                elong = float(body.elong)
                entry["elongation"] = round(math.degrees(elong), 2)
            except Exception:
                pass
        results["planets"].append(entry)

    for p in results["planets"]:
        if p["planet"] in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"):
            yesterday = ephem.Observer()
            yesterday.date = obs.date - 1
            body = dict(PLANETS)[p["planet"]]()
            body.compute(yesterday)
            _, _, prev_lon = ecliptic_to_zodiac(body.ra, body.dec, yesterday.date)
            p["retrograde"] = prev_lon > p["absolute_longitude"]

    outpath = f"data/transits_{date_str}.json"
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    main()
