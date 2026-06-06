import os

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv("env.env")

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def perform_research(
    queries: list[str],
    max_results: int = 3
) -> dict:
    """
    Execute Tavily searches for the generated queries
    and return additional information plus sources.
    """

    additional_information = []
    sources = []

    try:

        for query in queries:

            response = tavily_client.search(
                query=query,
                max_results=max_results
            )

            for result in response.get("results", []):

                content = result.get("content", "")
                url = result.get("url", "")

                if content:
                    additional_information.append(content)

                if url:
                    sources.append(url)

        # Remove duplicate sources
        sources = list(set(sources))

        return {
            "additional_information": additional_information,
            "sources": sources
        }

    except Exception as e:

        return {
            "error": str(e),
            "additional_information": [],
            "sources": []
        }