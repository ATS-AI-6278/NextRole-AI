import json
import logging
from typing import Any, Dict, Optional

import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self, model_name: str = "gemini-1.5-flash-latest"):
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not set. AI capabilities will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(model_name)

    async def generate_json(self, prompt: str, *, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a JSON response from the LLM.
        """
        if not self.model:
            return {}

        try:
            # Use generation_config to encourage JSON format.
            generation_config = {
                "response_mime_type": "application/json",
            }
            
            # If system_instruction was provided at init, we use a new model instance.
            # For simplicity in this common wrapper, we pass it in the prompt if needed.
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System Instruction: {system_instruction}\n\nUser Input: {prompt}"

            response = self.model.generate_content(
                full_prompt, 
                generation_config=generation_config
            )
            
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return {}

    async def generate_text(self, prompt: str) -> str:
        """
        Generates a simple text response.
        """
        if not self.model:
            return "AI service unavailable (API key missing)."

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"AI Text Generation Error: {e}")
            return "Error generating response."
