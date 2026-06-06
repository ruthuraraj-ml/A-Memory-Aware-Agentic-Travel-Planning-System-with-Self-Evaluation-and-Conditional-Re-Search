import os
import requests

from dotenv import load_dotenv
from langchain.tools import tool


load_dotenv("env.env")


WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


def get_weather(city: str) -> dict:
    """
    Fetch current weather information for a city.
    """

    url = "http://api.weatherapi.com/v1/current.json"

    params = {
        "key": WEATHER_API_KEY,
        "q": city,
        "aqi": "no"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
            "city": data["location"]["name"],
            "country": data["location"]["country"],
            "local_time": data["location"]["localtime"],
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"],
            "humidity": data["current"]["humidity"],
            "wind_kph": data["current"]["wind_kph"],
            "icon_url": f"https:{data['current']['condition']['icon']}"
        }

    except Exception as e:

        return {
            "error": str(e)
        }
    

@tool
def weather_tool(city: str):
    """
    Get current weather information
    for a destination.
    """

    return get_weather(city)