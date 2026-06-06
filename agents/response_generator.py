from llms.router import get_primary_llm
from utils.parser import extract_text


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builder — separated from generation so it can be tested independently
# ─────────────────────────────────────────────────────────────────────────────
def build_prompt(
    user_query: str,
    destination: str,
    trip_duration: str,
    travel_month: str,
    diet: str | None,
    travel_style: str | None,
    budget: str | None,
    transport: str | None,
    weather_data: dict,
    travel_data: dict,
    research_data: dict | None,
) -> str:
    """
    Constructs the full LLM prompt from structured inputs.
    Keeping this as a pure function makes it unit-testable without
    touching the LLM.
    """

    # ── Serialize only the fields the LLM actually needs ─────────────────────
    # Dumping the entire travel_data dict (including image URLs) bloats the
    # context with noise. Extract only text-relevant fields.
    attractions_text = "\n".join(
        f"- {a.get('name', 'Unknown')}: {a.get('description', '')}"
        for a in travel_data.get("attractions", [])
    )
    foods_text = "\n".join(
        f"- {f.get('name', 'Unknown')}: {f.get('description', '')}"
        for f in travel_data.get("foods", [])
    )

    additional_text = "None"
    if research_data:
        items = research_data.get("additional_information", [])
        if items:
            additional_text = "\n".join(f"- {item}" for item in items)

    # ── Preference block — only emit lines where value is set ────────────────
    prefs_lines = []
    if diet:
        prefs_lines.append(f"Diet: {diet}")
    if travel_style:
        prefs_lines.append(f"Travel Style: {travel_style}")
    if budget:
        prefs_lines.append(f"Budget: {budget}")
    if transport:
        prefs_lines.append(f"Transport: {transport}")
    prefs_block = "\n".join(prefs_lines) if prefs_lines else "No specific preferences provided."

    return f"""
You are an expert travel planner.
Generate a personalized, grounded travel guide using ONLY the information below.

========================
USER QUERY
========================
{user_query}

========================
TRAVELER PROFILE
========================
Destination:    {destination}
Trip Duration:  {trip_duration}
Travel Month:   {travel_month}

{prefs_block}

========================
WEATHER CONDITIONS
========================
Temperature:  {weather_data.get('temperature_c', weather_data.get('temp_c', 'N/A'))}°C
Condition:    {weather_data.get('condition', 'N/A')}
Humidity:     {weather_data.get('humidity', 'N/A')}%
Wind:         {weather_data.get('wind_kph', 'N/A')} km/h

========================
ATTRACTIONS
========================
{attractions_text or "No attractions data available."}

========================
LOCAL FOODS
========================
{foods_text or "No food data available."}

========================
ADDITIONAL RESEARCH
========================
{additional_text}

========================
PERSONALIZATION RULES
========================
Apply ONLY the preferences listed above. If a preference field is absent, do NOT assume one.

Diet:
- Vegetarian → prioritize vegetarian and plant-based dishes
- Vegan → prioritize fully vegan options; flag animal products

Travel Style:
- Foodie → emphasize local cuisine, markets, street food, and restaurants
- Culture → emphasize heritage sites, museums, traditions, and art
- Adventure → emphasize outdoor activities, hikes, and sports
- Nature → emphasize parks, landscapes, and scenic routes

Budget:
- Budget → affordable options only; mention free entry points
- Mid-range → balance comfort and affordability
- Luxury → suggest premium and exclusive experiences

Transport:
- Public Transport → buses, trains, metro; avoid taxi-only recommendations
- Taxi → include ride-hailing where useful
- Rental Vehicle → add driving notes and parking tips

========================
CONTENT RULES
========================
- Cite only attractions and foods from the ATTRACTIONS and LOCAL FOODS sections above.
- Do NOT invent place names, ratings, or prices.
- If data is missing for a section, state that clearly rather than fabricating.
- Keep each day's itinerary realistic in terms of travel time.

========================
OUTPUT FORMAT
========================
Use Markdown. Include exactly these sections in order:

# Traveler Profile
# Destination Overview
# Current Weather & Packing Tips
# Top Attractions
# Must-Try Local Foods
# Transportation Advice
# Seasonal Highlights
# Suggested {trip_duration} Itinerary
# Travel Tips & Warnings

Be concise, specific, and traveler-friendly.
Avoid generic filler sentences.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────
def generate_response(
    user_query: str,
    memory: dict,
    weather_data: dict,
    travel_data: dict,
    research_data: dict | None = None,
) -> str:
    """
    Generates the final Markdown travel guide.

    Changes from original:
    - Prompt builder extracted as a pure function (testable, reusable)
    - Travel data serialized to text-only fields before passing to LLM
      (removes image URLs, credits, and other non-text noise from context)
    - Preference block skips None values instead of passing the word 'None'
    - Output section renamed to include trip_duration for specificity
    - Added "Travel Tips & Warnings" section for practical edge cases
    """
    preferences = memory.get("preferences", {})

    prompt = build_prompt(
        user_query=user_query,
        destination=memory.get("destination", "Unknown"),
        trip_duration=memory.get("trip_duration", ""),
        travel_month=memory.get("travel_month", ""),
        diet=preferences.get("diet"),
        travel_style=preferences.get("travel_style"),
        budget=preferences.get("budget"),
        transport=preferences.get("transport"),
        weather_data=weather_data,
        travel_data=travel_data,
        research_data=research_data,
    )

    llm = get_primary_llm()
    response = llm.invoke(prompt)
    return extract_text(response)
