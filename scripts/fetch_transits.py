#!/usr/bin/env python3
"""Fetch today's geocentric planetary positions using PyEphem."""

import json
import math
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

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ZODIAC_GLYPHS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}


def ecliptic_longitude_to_zodiac(ra_radians: float, dec_radians: float, date) -> tuple[str, float, float]:
    """Convert equatorial coords to ecliptic longitude, then to zodiac sign + degree."""
    ecl = ephem.Ecliptic(ephem.Equatorial(ra_radians, dec_radians, epoch=date))
    lon_deg = math.degrees(float(ecl.lon))
    sign_index = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return ZODIAC_SIGNS[sign_index], degree_in_sign, lon_deg


def get_moon_phase(observer) -> dict:
    """Get current moon phase info."""
    moon = ephem.Moon(observer)
    phase_pct = moon.phase
    next_new = ephem.next_new_moon(observer.date)
    next_full = ephem.next_full_moon(observer.date)
    prev_new = ephem.previous_new_moon(observer.date)

    age_days = observer.date - prev_new

    if phase_pct < 1:
        phase_name = "New Moon"
    elif age_days < 7.4:
        phase_name = "Waxing Crescent"
    elif age_days < 10.8:
        phase_name = "First Quarter"
    elif age_days < 14.8:
        phase_name = "Waxing Gibbous"
    elif phase_pct > 98:
        phase_name = "Full Moon"
    elif age_days < 22.1:
        phase_name = "Waning Gibbous"
    elif age_days < 25.5:
        phase_name = "Last Quarter"
    else:
        phase_name = "Balsamic"

    return {
        "phase_name": phase_name,
        "illumination_pct": round(phase_pct, 1),
        "age_days": round(age_days, 1),
        "next_new_moon": str(ephem.Date(next_new)),
        "next_full_moon": str(ephem.Date(next_full)),
    }


def is_retrograde(body, observer) -> bool:
    """Check if a planet is retrograde by comparing positions over 1 day."""
    if isinstance(body, (ephem.Sun, ephem.Moon)):
        return False
    d = observer.date
    body.compute(observer)
    ecl1 = ephem.Ecliptic(ephem.Equatorial(body.ra, body.dec, epoch=d))
    lon1 = float(ecl1.lon)

    observer.date = d + 1
    body.compute(observer)
    ecl2 = ephem.Ecliptic(ephem.Equatorial(body.ra, body.dec, epoch=d + 1))
    lon2 = float(ecl2.lon)

    observer.date = d
    body.compute(observer)

    diff = lon2 - lon1
    if diff > math.pi:
        diff -= 2 * math.pi
    elif diff < -math.pi:
        diff += 2 * math.pi
    return diff < 0


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    observer = ephem.Observer()
    observer.date = now.strftime("%Y/%m/%d %H:%M:%S")
    observer.lat = "0"
    observer.lon = "0"

    positions = {}
    for name, planet_class in PLANETS.items():
        body = planet_class(observer)
        sign, degree, abs_lon = ecliptic_longitude_to_zodiac(body.ra, body.dec, observer.date)
        retro = is_retrograde(planet_class(), observer)
        positions[name] = {
            "sign": sign,
            "glyph": ZODIAC_GLYPHS[sign],
            "degree": round(degree, 2),
            "absolute_longitude": round(abs_lon, 2),
            "retrograde": retro,
            "formatted": f"{degree:.0f}°{sign[:3]} {'Rx' if retro else ''}".strip(),
        }

    moon_phase = get_moon_phase(observer)

    output = {
        "date": date_str,
        "timestamp_utc": now.isoformat(),
        "planets": positions,
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
