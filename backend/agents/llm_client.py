import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("careflow.llm")

# Get API key from env or default
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyALsTLQ1an4i6ZHrIuDyo5noimexq3g864")

_client = None

def get_client():
    global _client
    if _client is None:
        try:
            from google import genai
            _client = genai.Client(api_key=API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize google.genai Client: {e}")
            _client = None
    return _client

def clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def generate_json_response(system_instruction: str, prompt: str, default_factory=None) -> dict:
    """
    Invokes Gemini 2.5 Flash and returns parsed JSON.
    Falls back to default_factory() if any API/network/parsing error occurs.
    """
    client = get_client()
    if client:
        try:
            full_prompt = f"{system_instruction}\n\nStrict requirement: Output ONLY raw valid JSON with no markdown backticks.\n\nInput Context:\n{prompt}"
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            raw = clean_json_text(response.text or "")
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Gemini API call or parsing failed ({e}), using specialist fallback response.")

    if default_factory:
        return default_factory()

    return {"status": "completed", "error": "LLM response could not be parsed"}
