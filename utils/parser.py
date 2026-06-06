def extract_text(response):

    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return content[0]["text"]

    return str(content)

def clean_json_response(text):

    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace(
            "```json",
            "",
            1
        )

    if cleaned.startswith("```"):
        cleaned = cleaned.replace(
            "```",
            "",
            1
        )

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()