#!/usr/bin/env python3

import json
import os
from datetime import datetime
from urllib.parse import quote

import requests

WEATHER_CODES = {
    '113': '☀️',
    '116': '⛅️',
    '119': '☁️',
    '122': '☁️',
    '143': '🌫',
    '176': '🌦',
    '179': '🌧',
    '182': '🌧',
    '185': '🌧',
    '200': '⛈',
    '227': '🌨',
    '230': '❄️',
    '248': '🌫',
    '260': '🌫',
    '263': '🌦',
    '266': '🌦',
    '281': '🌧',
    '284': '🌧',
    '293': '🌦',
    '296': '🌦',
    '299': '🌧',
    '302': '🌧',
    '305': '🌧',
    '308': '🌧',
    '311': '🌧',
    '314': '🌧',
    '317': '🌧',
    '320': '🌨',
    '323': '🌨',
    '326': '🌨',
    '329': '❄️',
    '332': '❄️',
    '335': '❄️',
    '338': '❄️',
    '350': '🌧',
    '353': '🌦',
    '356': '🌧',
    '359': '🌧',
    '362': '🌧',
    '365': '🌧',
    '368': '🌨',
    '371': '❄️',
    '374': '🌧',
    '377': '🌧',
    '386': '⛈',
    '389': '🌩',
    '392': '⛈',
    '395': '❄️'
}

DEFAULT_TEXT = "N/A"
DEFAULT_TOOLTIP = "Weather unavailable"


def fetch_weather():
    location = os.environ.get("WTTR_LOCATION", "").strip()
    target = quote(location) if location else ""
    url = f"https://wttr.in/{target}?format=j1"
    response = requests.get(
        url,
        headers={"User-Agent": "waybar-wttr/1.0"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def format_time(time):
    return time.replace("00", "").zfill(2)


def format_temp(temp):
    return f"{temp}°".ljust(3)


def format_chances(hour):
    chances = {
        "chanceoffog": "Fog",
        "chanceoffrost": "Frost",
        "chanceofovercast": "Overcast",
        "chanceofrain": "Rain",
        "chanceofsnow": "Snow",
        "chanceofsunshine": "Sunshine",
        "chanceofthunder": "Thunder",
        "chanceofwindy": "Wind"
    }

    conditions = []
    for event in chances.keys():
        if int(hour[event]) > 0:
            conditions.append(chances[event]+" "+hour[event]+"%")
    return ", ".join(conditions)


def fallback_payload():
    return {"text": DEFAULT_TEXT, "tooltip": DEFAULT_TOOLTIP}


def main():
    try:
        weather = fetch_weather()
        current = weather["current_condition"][0]
    except Exception:
        print(json.dumps(fallback_payload()))
        return

    data = {}
    icon = WEATHER_CODES.get(current.get("weatherCode", ""), "☁️")
    feels_like = current.get("FeelsLikeF") or current.get("FeelsLikeC") or DEFAULT_TEXT
    current_temp = current.get("temp_F") or current.get("temp_C") or DEFAULT_TEXT

    data["text"] = f"{icon} {feels_like}°"
    data["tooltip"] = (
        f"<b>{current['weatherDesc'][0]['value']} {current_temp}°</b>\n"
        f"Feels like: {feels_like}°\n"
        f"Wind: {current.get('windspeedKmph', DEFAULT_TEXT)}Km/h\n"
        f"Humidity: {current.get('humidity', DEFAULT_TEXT)}%\n"
    )

    for i, day in enumerate(weather.get("weather", [])):
        data["tooltip"] += "\n<b>"
        if i == 0:
            data["tooltip"] += "Today, "
        if i == 1:
            data["tooltip"] += "Tomorrow, "
        data["tooltip"] += f"{day['date']}</b>\n"
        data["tooltip"] += f"⬆️ {day['maxtempC']}° ⬇️ {day['mintempC']}° "
        data["tooltip"] += f" {day['astronomy'][0]['sunrise']}  {day['astronomy'][0]['sunset']}\n"
        for hour in day["hourly"]:
            if i == 0 and int(format_time(hour["time"])) < datetime.now().hour - 2:
                continue
            icon = WEATHER_CODES.get(hour.get("weatherCode", ""), "☁️")
            data["tooltip"] += (
                f"{format_time(hour['time'])} {icon} {format_temp(hour['FeelsLikeC'])} "
                f"{hour['weatherDesc'][0]['value']}, {format_chances(hour)}\n"
            )

    print(json.dumps(data))


if __name__ == "__main__":
    main()
