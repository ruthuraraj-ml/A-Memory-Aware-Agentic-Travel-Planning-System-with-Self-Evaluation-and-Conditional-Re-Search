import streamlit as st
from pathlib import Path
from memory.session_memory import create_memory
from agents.langgraph_workflow import travel_agent_app
from agents.response_generator import generate_response

# ─────────────────────────────────────────────
# 1. Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Reflective Travel Assistant",
    page_icon="✈️",
    layout="wide"
)

# ─────────────────────────────────────────────
# 2. CSS Loading
# ─────────────────────────────────────────────
current_dir = Path(__file__).resolve().parent
css_path = current_dir.parent / "assets" / "styles.css"

try:
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ─────────────────────────────────────────────
# 3. Session State Initialization
# ─────────────────────────────────────────────
if "memory" not in st.session_state:
    st.session_state.memory = create_memory()

if "result" not in st.session_state:
    st.session_state.result = None

if "travel_guide" not in st.session_state:
    st.session_state.travel_guide = None

# ─────────────────────────────────────────────
# 4. Hero Banner
# ─────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>✈️ Reflective Travel Assistant</h1>
        <p>AI-powered personalized travel planning with reflection, re-search, and memory.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
# 5. Sidebar — Traveler Preferences
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Traveler Preferences")

    destination = st.text_input("Destination", "Kyoto")

    trip_duration = st.selectbox(
        "Trip Duration",
        ["1 Day", "3 Days", "5 Days", "1 Week"]
    )

    travel_month = st.selectbox(
        "Travel Month",
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
    )

    diet          = st.selectbox("Diet Preference", [None, "Vegetarian", "Vegan"])
    travel_style  = st.selectbox("Travel Style",    [None, "Foodie", "Culture", "Adventure", "Nature"])
    budget        = st.selectbox("Budget",           [None, "Budget", "Mid-range", "Luxury"])
    transport     = st.selectbox("Transport",        [None, "Public Transport", "Taxi", "Rental Vehicle"])

    st.session_state.memory.update(
        {
            "destination":    destination,
            "trip_duration":  trip_duration,
            "travel_month":   travel_month,
            "preferences": {
                "diet":          diet,
                "travel_style":  travel_style,
                "budget":        budget,
                "transport":     transport,
            }
        }
    )

    # ── Reset button — clears cached results when preferences change ──────
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.result       = None
        st.session_state.travel_guide = None
        st.rerun()

# ─────────────────────────────────────────────
# 6. Query Input
# ─────────────────────────────────────────────
query = st.text_area(
    "Describe your trip",
    f"Plan a {trip_duration} trip to {destination} in {travel_month}"
)

generate = st.button("✈️ Generate Travel Plan", use_container_width=True)

# ─────────────────────────────────────────────
# 7. Agent Execution
# ─────────────────────────────────────────────
if generate:
    st.session_state.result       = None
    st.session_state.travel_guide = None

    progress_status = st.empty()

    with progress_status.container():
        st.info("🤖 Spawning Autonomous Agent State Machine...")

    result = travel_agent_app.invoke(
        {
            "destination":  destination,
            "user_query":   query,
            "memory":       st.session_state.memory,
            "cycle":        0,
            "logs":         [],
            "reflection_history": [],
            "data_confidence":    0.0,
        }
    )

    with progress_status.container():
        st.info("✍️ Reasoning complete. Synthesizing final response guide...")

    travel_guide = generate_response(
        query,
        st.session_state.memory,
        result["weather_data"],
        result["travel_data"],
        result.get("research_data")
    )

    progress_status.empty()

    # Persist to session so results survive sidebar interaction
    st.session_state.result       = result
    st.session_state.travel_guide = travel_guide

# ─────────────────────────────────────────────
# 8. Results Rendering
# Only runs when results exist in session state
# ─────────────────────────────────────────────
if st.session_state.result and st.session_state.travel_guide:
    result       = st.session_state.result
    travel_guide = st.session_state.travel_guide

    attractions_list = result["travel_data"].get("attractions", [])
    hero_image = attractions_list[0].get("image_url") if attractions_list else None

    if hero_image:
        st.image(hero_image, use_container_width=True)

    st.title(f"📍 Discover {destination}")
    st.subheader(f"⏱️ {trip_duration} in {travel_month}")

    # ── Confidence badge (new) ────────────────────────────────────────────
    confidence = result.get("data_confidence", 0.0)
    confidence_pct = int(confidence * 100)
    badge_color = (
        "green"  if confidence_pct >= 80 else
        "orange" if confidence_pct >= 50 else
        "red"
    )
    st.markdown(
        f"<span style='background:{badge_color};color:white;"
        f"padding:3px 10px;border-radius:12px;font-size:0.8rem;'>"
        f"🧠 Agent Confidence: {confidence_pct}%</span>",
        unsafe_allow_html=True
    )

    st.write("---")

    # ── Tabs ─────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 AI Travel Guide",
        "🏛️ Top Attractions",
        "🍱 Must-Try Foods",
        "🕵️ Agent Insights"
    ])

    # ── TAB 1: Travel Guide ───────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="section-title">Current Weather</div>', unsafe_allow_html=True)
        weather = result["weather_data"]
        w_c1, w_c2, w_c3, w_c4 = st.columns(4)
        w_c1.metric("Temperature", f"{weather.get('temperature_c', weather.get('temp_c', 'N/A'))} °C")
        w_c2.metric("Condition",   weather.get("condition", "N/A"))
        w_c3.metric("Humidity",    f"{weather.get('humidity', 'N/A')}%")
        w_c4.metric("Wind",        f"{weather.get('wind_kph', 'N/A')} km/h")

        st.write("---")

        st.markdown('<div class="section-title">Traveler Profile Context</div>', unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns(4)
        p1.markdown(f'<div class="profile-card"><h3>🥗 Diet</h3><p>{diet or "None specified"}</p></div>',          unsafe_allow_html=True)
        p2.markdown(f'<div class="profile-card"><h3>🍜 Style</h3><p>{travel_style or "None specified"}</p></div>', unsafe_allow_html=True)
        p3.markdown(f'<div class="profile-card"><h3>💰 Budget</h3><p>{budget or "None specified"}</p></div>',      unsafe_allow_html=True)
        p4.markdown(f'<div class="profile-card"><h3>🚌 Transit</h3><p>{transport or "None specified"}</p></div>',  unsafe_allow_html=True)

        st.write("---")

        st.markdown('<div class="section-title">Your Custom Itinerary</div>', unsafe_allow_html=True)
        st.markdown(travel_guide)

        # ── Download button ───────────────────────────────────────────────
        st.download_button(
            label="📥 Download Itinerary (.md)",
            data=travel_guide,
            file_name=f"{destination.lower().replace(' ', '_')}_travel_guide.md",
            mime="text/markdown",
            use_container_width=True
        )

    # ── TAB 2: Attractions ────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-title">Curated Sightseeing Locations</div>', unsafe_allow_html=True)

        if not attractions_list:
            st.warning("No attraction data was returned for this destination.")
        else:
            attraction_cols = st.columns(3)
            for idx, attraction in enumerate(attractions_list):
                with attraction_cols[idx % 3]:
                    if attraction.get("image_url"):
                        st.image(attraction["image_url"], use_container_width=True)
                    st.subheader(attraction.get("name", "Unknown Attraction"))
                    st.caption(attraction.get("description", ""))
                    if attraction.get("credit"):
                        st.markdown(
                            f"<small style='color:gray;'>📸 {attraction['credit']} via Pexels</small>",
                            unsafe_allow_html=True
                        )

    # ── TAB 3: Foods ──────────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-title">Local Culinary Recommendations</div>', unsafe_allow_html=True)
        food_list = result["travel_data"].get("foods", [])

        if not food_list:
            st.warning("No food data was returned for this destination.")
        else:
            food_cols = st.columns(3)
            for idx, food in enumerate(food_list):
                with food_cols[idx % 3]:
                    if food.get("image_url"):
                        st.image(food["image_url"], use_container_width=True)
                    st.subheader(food.get("name", "Unknown Food"))
                    st.caption(food.get("description", ""))
                    if food.get("credit"):
                        st.markdown(
                            f"<small style='color:gray;'>📸 {food['credit']} via Pexels</small>",
                            unsafe_allow_html=True
                        )

    # ── TAB 4: Agent Insights ─────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-title">State Machine Execution Sequence</div>', unsafe_allow_html=True)
        st.write(
            "This log outlines how the agent's internal reasoning loop decided "
            "to query, evaluate, and fulfill your trip details using explicit graph conditions."
        )

        # ── Reflection history timeline (new) ────────────────────────────
        history = result.get("reflection_history", [])
        if history:
            st.markdown("#### Reflection History")
            for entry in history:
                icon   = "✅" if entry["status"] == "SUFFICIENT" else "🔄"
                c_pct  = int(entry["confidence"] * 100)
                label  = f"{icon} Cycle {entry['cycle']} — {entry['status']} ({c_pct}% confidence)"
                with st.expander(label, expanded=False):
                    if entry["missing"]:
                        st.markdown("**Gaps identified:**")
                        for gap in entry["missing"]:
                            st.markdown(f"- {gap}")
                    else:
                        st.success("No information gaps detected.")
            st.write("---")

        # ── Raw execution log ─────────────────────────────────────────────
        st.markdown("#### Execution Log")
        for log in result.get("logs", []):
            st.info(f"⚙️ {log}")

        # ── Research sources (new) ────────────────────────────────────────
        research_data = result.get("research_data")
        if research_data:
            sources = research_data.get("sources", [])
            if sources:
                st.write("---")
                st.markdown("#### Research Sources Used")
                for src in sources:
                    st.markdown(f"- {src}")
