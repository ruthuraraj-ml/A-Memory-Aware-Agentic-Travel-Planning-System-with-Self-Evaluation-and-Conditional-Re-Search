# tools/image_tool.py
import os
import requests
from dotenv import load_dotenv

load_dotenv("env.env")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


def fetch_image_data(query: str) -> dict:
    """
    Fetch a representative image metadata packet from Pexels.
    Returns a unified fallback dictionary if the API key is missing or an error occurs.
    """
    fallback = {
        "image_url": None,
        "credit": None,
        "source": "Pexels"
    }

    if not PEXELS_API_KEY:
        return fallback

    url = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    params = {
        "query": query,
        "per_page": 1
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        photos = data.get("photos", [])

        if not photos:
            return fallback

        photo = photos[0]

        return {
            "image_url": photo["src"]["large"],
            "credit": photo.get("photographer"),
            "source": "Pexels"
        }

    except Exception as e:
        print(f"Pexels Error: {e}")
        return fallback


def enrich_travel_data_with_images(travel_data: dict) -> dict:
    """
    Iterates through discovered attractions and foods inside travel_data,
    fetches their specific image metadata from Pexels, and merges it inline.
    """
    # 1. Enrich Attractions
    attractions = travel_data.get("attractions", [])
    for attraction in attractions:
        name = attraction.get("name")
        if not name:
            continue

        image_data = fetch_image_data(name)
        attraction.update(image_data)

    # 2. Enrich Foods (appending 'food' for contextualized image searching)
    foods = travel_data.get("foods", [])
    for food in foods:
        name = food.get("name")
        if not name:
            continue

        image_data = fetch_image_data(f"{name} food")
        food.update(image_data)

    return travel_data