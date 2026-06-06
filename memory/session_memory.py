def create_memory() -> dict:
    """
    Create a fresh memory object
    for the travel assistant.
    """

    return {

        "destination": None,

        "trip_duration": None,

        "travel_month": None,

        "preferences": {

            "diet": None,

            "travel_style": None,

            "budget": None,

            "transport": None
        }
    }