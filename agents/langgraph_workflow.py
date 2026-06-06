from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END

from tools.weather_tool import get_weather
from tools.discovery_tool import discover_destination
from tools.image_tool import enrich_travel_data_with_images
from reflection.reflector import reflect
from research.query_generator import generate_queries
from research.researcher import perform_research

MAX_REFLECTION_CYCLES = 2


# ─────────────────────────────────────────────
# Log reducer — appends instead of overwriting
# ─────────────────────────────────────────────
def append_log(current_logs: list, new_logs: list) -> list:
    return current_logs + new_logs


# ─────────────────────────────────────────────
# Typed State — strict field declarations
# ─────────────────────────────────────────────
class TravelAgentState(TypedDict):
    destination: str
    user_query: str
    memory: dict
    weather_data: dict
    travel_data: dict
    research_data: dict
    reflection_result: dict
    cycle: int
    reflection_history: list[dict]   # NEW: tracks every reflection verdict
    data_confidence: float            # NEW: 0.0–1.0 score from reflector
    logs: Annotated[list[str], append_log]


# ─────────────────────────────────────────────
# NODE 1 — Initial Collection
# ─────────────────────────────────────────────
def initial_collection_node(state: TravelAgentState) -> dict:
    destination = state["destination"]
    weather = get_weather(destination)
    travel = discover_destination(destination)

    return {
        "weather_data": weather,
        "travel_data": travel,
        "reflection_history": [],      # initialise clean slate
        "data_confidence": 0.0,
        "logs": [
            "Fetching weather data...",
            "Discovering destination information..."
        ]
    }


# ─────────────────────────────────────────────
# NODE 2 — Reflection
# Evaluates data quality; records verdict in history
# ─────────────────────────────────────────────
def reflection_node(state: TravelAgentState) -> dict:
    current_travel_data = {**state["travel_data"]}

    research_data = state.get("research_data")
    if research_data:
        current_travel_data["additional_information"] = research_data.get(
            "additional_information", []
        )

    result = reflect(
        state["user_query"],
        state["weather_data"],
        current_travel_data
    )

    # ── Confidence scoring ──────────────────────────────────────────────
    # Derive a simple 0–1 score from the reflector's missing_information
    # list so the UI can display how confident the agent is.
    missing = result.get("missing_information", [])
    confidence = round(max(0.0, 1.0 - (len(missing) * 0.2)), 2)

    # ── Append to history so every cycle is traceable ───────────────────
    history_entry = {
        "cycle": state.get("cycle", 0),
        "status": result["status"],
        "missing": missing,
        "confidence": confidence
    }
    updated_history = state.get("reflection_history", []) + [history_entry]

    # ── Friendly log label ───────────────────────────────────────────────
    confidence_pct = int(confidence * 100)
    log_msg = (
        f"Reflection Result: {result['status']} "
        f"(confidence {confidence_pct}%)"
    )
    if missing:
        log_msg += f" — gaps: {', '.join(missing)}"

    return {
        "reflection_result": result,
        "reflection_history": updated_history,
        "data_confidence": confidence,
        "logs": [log_msg]
    }


# ─────────────────────────────────────────────
# NODE 3 — Research
# Deduplicates by content hash to avoid noise
# ─────────────────────────────────────────────
def _deduplicate(items: list[str]) -> list[str]:
    """Remove near-duplicate strings using a simple set on stripped text."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def research_node(state: TravelAgentState) -> dict:
    current_cycle = state.get("cycle", 0) + 1

    queries = generate_queries(
        state["destination"],
        state["reflection_result"]["missing_information"]
    )

    new_research = perform_research(queries)
    existing = state.get("research_data") or {}

    # Deduplicated merge (improvement over raw list concatenation)
    combined_information = _deduplicate(
        existing.get("additional_information", []) +
        new_research.get("additional_information", [])
    )

    combined_sources = list(
        set(
            existing.get("sources", []) +
            new_research.get("sources", [])
        )
    )

    return {
        "research_data": {
            "additional_information": combined_information,
            "sources": combined_sources
        },
        "cycle": current_cycle,
        "logs": [
            f"Reflection Cycle {current_cycle}",
            f"Generated {len(queries)} queries",
            f"Researched {len(combined_information)} unique information items",
            "Additional research completed"
        ]
    }


# ─────────────────────────────────────────────
# NODE 4 — Image Enrichment
# ─────────────────────────────────────────────
def image_enrichment_node(state: TravelAgentState) -> dict:
    enriched = enrich_travel_data_with_images(state["travel_data"])

    attraction_count = len(enriched.get("attractions", []))
    food_count = len(enriched.get("foods", []))

    return {
        "travel_data": enriched,
        "logs": [
            f"Images enriched — {attraction_count} attractions, {food_count} foods"
        ]
    }


# ─────────────────────────────────────────────
# ROUTER — after reflection
# Three-way: research | force-finish | finish
# ─────────────────────────────────────────────
def route_after_reflection(state: TravelAgentState) -> str:
    result = state["reflection_result"]
    cycle = state.get("cycle", 0)

    if result["status"] == "INSUFFICIENT":
        if cycle < MAX_REFLECTION_CYCLES:
            return "research"
        # Hit ceiling — log it explicitly and proceed
        # (log injection here is a side-effect; nodes are the right place,
        #  but routers can't mutate state — the ceiling case is captured
        #  in reflection_history already)
        return "finish"

    return "finish"


# ─────────────────────────────────────────────
# Graph Assembly
# ─────────────────────────────────────────────
workflow = StateGraph(TravelAgentState)

workflow.add_node("initial_collection", initial_collection_node)
workflow.add_node("reflection", reflection_node)
workflow.add_node("research", research_node)
workflow.add_node("images", image_enrichment_node)

workflow.add_edge(START, "initial_collection")
workflow.add_edge("initial_collection", "reflection")

workflow.add_conditional_edges(
    "reflection",
    route_after_reflection,
    {
        "research": "research",
        "finish": "images"
    }
)

workflow.add_edge("research", "reflection")
workflow.add_edge("images", END)

travel_agent_app = workflow.compile()
