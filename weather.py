"""Fetch the weather for a city on a random day in the past year and format it as a short text."""
from __future__ import annotations

import json
import random
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# WMO weather codes -> description
WMO = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "freezing fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 56: "freezing drizzle", 57: "heavy freezing drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 66: "freezing rain", 67: "heavy freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains",
    80: "light showers", 81: "showers", 82: "violent showers", 85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
}


def random_day(today: date, rng: random.Random | None = None) -> date:
    """A random day in the past year. Stops 7 days back because the archive lags a few days."""
    return today - timedelta(days=(rng or random).randint(7, 365))


def load_cities(path: str | Path = Path(__file__).with_name("cities.json")) -> list[dict]:
    return json.loads(Path(path).read_text())


def fetch_day(city: dict, day: date) -> dict:
    q = urllib.parse.urlencode({
        "latitude": city["lat"], "longitude": city["lon"],
        "start_date": day.isoformat(), "end_date": day.isoformat(),
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch",
        "timezone": city["timezone"],
    })
    with urllib.request.urlopen(f"{ARCHIVE_URL}?{q}", timeout=30) as r:
        daily = json.load(r)["daily"]
    return {k: v[0] for k, v in daily.items() if k != "time"}


def build_message(city: dict, day: date, w: dict) -> str:
    desc = WMO.get(w["weather_code"], "unknown conditions").capitalize()
    precip = w["precipitation_sum"] or 0
    rain = f"{precip:.2f} in precip" if precip else "no precip"
    return (
        f"Weather update: {day:%b %-d, %Y} in {city['name']}, {city['country']}. "
        f"{desc}. High {w['temperature_2m_max']:.0f}F, low {w['temperature_2m_min']:.0f}F, "
        f"{rain}, winds up to {w['wind_speed_10m_max']:.0f} mph."
    )


def report_for(city: dict | None = None, today: date | None = None, rng: random.Random | None = None) -> str:
    city = city or (rng or random).choice(load_cities())
    today = today or datetime.now(ZoneInfo(city["timezone"])).date()
    day = random_day(today, rng)
    return build_message(city, day, fetch_day(city, day))


if __name__ == "__main__":
    for _ in range(3):
        print(report_for())
