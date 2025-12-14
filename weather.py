import requests
from datetime import datetime

API_KEY = "3efdcefb3912ea9ac711e87c13481b17"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_current_weather(city="Bucharest"):
    """
    Returnează un dicționar cu datele meteo relevante pentru recomandări.
    """
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ro"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return None

    weather_main = data["weather"][0]["main"].lower()

    weather_info = {
        "city": city,
        "temperature": round(data["main"]["temp"]),
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"],
        "condition": weather_main,   # rain / snow / clear / clouds
        "is_rainy": weather_main in ["rain", "drizzle", "thunderstorm"],
        "is_snowy": weather_main == "snow",
        "season": get_season()
    }

    return weather_info


def get_season():
    month = datetime.now().month

    if month in [12, 1, 2]:
        return "Iarna"
    elif month in [3, 4, 5]:
        return "Primavara"
    elif month in [6, 7, 8]:
        return "Vara"
    else:
        return "Toamna"