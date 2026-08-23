import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def create_gemini_client() -> genai.Client:
    """Create a Gemini client using the API key from the environment."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    return genai.Client(api_key=api_key)