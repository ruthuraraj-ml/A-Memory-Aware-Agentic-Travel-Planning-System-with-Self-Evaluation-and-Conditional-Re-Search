import json

from llms.router import get_primary_llm
from utils.parser import (
    extract_text, 
    clean_json_response
    )


def reflect(
    user_query: str,
    weather_data: dict,
    travel_data: dict
) -> dict:
    """
    Evaluate whether enough information has been collected
    to answer the user's travel request.
    """

    prompt = f"""
    You are a travel information evaluator.

    USER QUERY:
    {user_query}

    WEATHER DATA:
    {weather_data}

    TRAVEL DATA:
    {travel_data}

    Determine whether enough information exists to answer
    the user's request completely.

    Consider:

    1. Weather
    2. Attractions
    3. Local Cuisine
    4. Travel Tips
    5. Transportation Information (if relevant)
    6. Seasonal Events (if relevant)

    Return ONLY valid JSON.

    Example:

    {{
        "status": "SUFFICIENT",
        "confidence": 95,
        "missing_information": []
    }}

    or

    {{
        "status": "INSUFFICIENT",
        "confidence": 60,
        "missing_information": [
            "Seasonal events",
            "Transportation advice"
        ]
    }}
    """

    llm = get_primary_llm()

    response = llm.invoke(prompt)

    try:

        cleaned_response = extract_text(response).strip()

        cleaned_response = clean_json_response(cleaned_response).strip()

        return json.loads(cleaned_response)

    except Exception as e:

        return {
            "status": "ERROR",
            "confidence": 0,
            "missing_information": [],
            "error": str(e),
            "raw_response": response.content
        }