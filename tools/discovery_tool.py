import os
import json

from dotenv import load_dotenv
from tavily import TavilyClient

from llms.router import get_fast_llm
from langchain.tools import tool


load_dotenv("env.env")

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def discover_destination(city: str) -> dict:
    """
    Discover attractions, cuisine and travel tips
    for a destination using Tavily + Groq.
    """

    attractions_results = tavily_client.search(
        query=f"Top tourist attractions in {city}",
        max_results=5
    )

    cuisine_results = tavily_client.search(
        query=f"Must try local foods in {city}",
        max_results=5
    )

    tips_results = tavily_client.search(
        query=f"Travel tips for tourists visiting {city}",
        max_results=5
    )

    combined_context = f"""
    DESTINATION: {city}

    ATTRACTIONS:
    {attractions_results}

    CUISINE:
    {cuisine_results}

    TRAVEL TIPS:
    {tips_results}
    """

    prompt = f"""
    You are a travel information extraction assistant.

    Extract:

    1. Top 5 attractions
    2. Top 5 local foods
    3. Top 5 travel tips

    Return ONLY valid JSON.

    Format:

    {{
      "destination": "{city}",

      "attractions": [
        {{
          "name": "",
          "description": ""
        }}
      ],

      "foods": [
        {{
          "name": "",
          "description": ""
        }}
      ],

      "travel_tips": [],

      "sources": []
    }}

    Search Results:

    {combined_context}
    """

    llm = get_fast_llm()

    response = llm.invoke(prompt)

    try:

        cleaned_response = response.content.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response.replace(
                "```json",
                ""
            )

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        return json.loads(cleaned_response)

    except Exception as e:

        return {
            "error": str(e),
            "raw_response": response.content
        }
    

@tool
def destination_discovery_tool(city: str):
    """
    Discover attractions, food and travel tips.
    """

    return discover_destination(city)