import json

from llms.router import get_fast_llm
from utils.parser import (
    extract_text, 
    clean_json_response
    )


def generate_queries(
    destination: str,
    missing_information: list
) -> list:
    """
    Generate targeted search queries
    from reflection gaps.
    """

    prompt = f"""
    You are a search query generation assistant.

    Destination:
    {destination}

    Missing Information:
    {missing_information}

    Generate targeted search queries
    that will help gather the missing information.

    Return ONLY valid JSON.

    Example:

    {{
        "queries": [
            "Kyoto July festivals",
            "Kyoto transportation tips",
            "Kyoto summer weather advice"
        ]
    }}
    """

    llm = get_fast_llm()

    response = llm.invoke(prompt)

    content = response.content

    cleaned_response = extract_text(response)
    
    cleaned_response = clean_json_response(cleaned_response)

    result = json.loads(cleaned_response)

    return result["queries"][:5]