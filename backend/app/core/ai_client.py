import re
import json
import logging
from typing import Any, Dict, Optional

from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not set. AI capabilities will be disabled.")
            self.client = None
        else:
            # Strictly using the new SDK
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            # User specified models - Strictly using these two
            self.LITE_MODEL = "gemini-3.1-flash-lite-preview"
            self.GEMMA_MODEL = "gemma-3-27b-it"

    async def generate_json(self, prompt: str, *, system_instruction: Optional[str] = None, model_type: str = "lite") -> Dict[str, Any]:
        """
        Generates a JSON response from the LLM using the new google-genai SDK.
        model_type: "lite" or "gemma"
        """
        if not self.client:
            return {}

        model_id = self.GEMMA_MODEL if model_type == "gemma" else self.LITE_MODEL

        try:
            # The new SDK uses client.models.generate_content
            config = {}
            if model_id.startswith("gemini"):
                config["response_mime_type"] = "application/json"
            
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config
            )
            
            # Robust JSON extraction from the response text
            text = response.text.strip()
            # Find the first { or [ and the last } or ]
            json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI Generation Error (type={model_type}): {e}")
            return {}

    async def generate_text(self, prompt: str, model_type: str = "lite") -> str:
        """
        Generates a simple text response using the new google-genai SDK.
        """
        if not self.client:
            return "AI service unavailable (API key missing)."

        model_id = self.GEMMA_MODEL if model_type == "gemma" else self.LITE_MODEL

        try:
            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"AI Text Generation Error (type={model_type}): {e}")
            return "Error generating response."
