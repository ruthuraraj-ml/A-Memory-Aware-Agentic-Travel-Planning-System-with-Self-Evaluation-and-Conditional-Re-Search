from agents.langgraph_workflow import travel_agent_app
from agents.response_generator import generate_response

user_query = "Plan a 3-day trip to Kyoto in July"

# 1. Execute the LangGraph StateGraph
result = travel_agent_app.invoke(
    {
        "destination": "Kyoto",
        "user_query": user_query,
        "cycle": 0,
        "logs": [],
        "weather_data": {},     # Optional: Initialize empty defaults
        "travel_data": {},      # Optional: Initialize empty defaults
        "research_data": {}     # Optional: Initialize empty defaults
    }
)

# 2. Extract and Pass variables using the correct state keys
final_response = generate_response(
    user_query=user_query,
    memory={
        "destination": "Kyoto",
        "trip_duration": "3 days",
        "travel_month": "July",
        "preferences": {
            "diet": None,
            "travel_style": None,
            "budget": None,
            "transport": None
        }
    },
    # FIX: Swapped result["weather"] to result["weather_data"]
    weather_data=result["weather_data"], 
    travel_data=result["travel_data"],
    research_data=result.get("research_data")  # Using .get() safely handles cases where research never ran
)

print(final_response)