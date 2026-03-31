import re
import json
import logging
import asyncio
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
            
            # User specified models - Strictly using these two primary models
            self.LITE_MODEL = "gemini-3.1-flash-lite-preview"
            self.GEMMA_MODEL = "gemma-3-27b-it"
            # Fallback model for high demand spikes
            self.BACKUP_MODEL = "gemini-1.5-flash"

    async def generate_json(self, prompt: str, *, system_instruction: Optional[str] = None, model_type: str = "lite") -> Dict[str, Any]:
        """
        Generates a JSON response from the LLM with built-in retries and fallback.
        """
        if not self.client:
            return {}

        model_id = self.GEMMA_MODEL if model_type == "gemma" else self.LITE_MODEL
        
        for attempt in range(5):
            try:
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
                
                text = response.text.strip()
                
                # Aggressively strip markdown
                if text.startswith("```json"):
                    text = text.replace("```json", "", 1).strip()
                if text.endswith("```"):
                    text = text[:-3].strip()

                # Grab array if starts with [, else object
                if text.startswith("["):
                    json_match = re.search(r'(\[.*\])', text, re.DOTALL)
                else:
                    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
                    
                if json_match:
                    text = json_match.group(1)
                
                try:
                    data = json.loads(text)
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON for {model_id}. Text: {text[:200]}")
                    # If it's garbled, let the loop retry
                    raise je

                if isinstance(data, list):
                    # We are expecting lists for batches now, so return the list itself!
                    return data
                
                return data if isinstance(data, dict) else {}

            except Exception as e:
                err_str = str(e).lower()
                is_retryable = any(x in err_str for x in ["503", "unavailable", "429", "rate limit", "overloaded"])
                
                if is_retryable and attempt < 4:
                    wait_time = 2 ** attempt
                    logger.warning(f"AI Service Busy ({model_id}, attempt {attempt+1}/5). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    # Switch to backup model if primary remains busy
                    if attempt >= 2 and model_type == "lite":
                        model_id = self.BACKUP_MODEL
                    continue
                
                logger.error(f"AI Generation Error (type={model_type}): {e}")
                return {}
        return {}

    async def generate_text(self, prompt: str, model_type: str = "lite") -> str:
        """
        Generates a text response with built-in retries and fallback.
        """
        if not self.client:
            return "AI service unavailable (API key missing)."

        model_id = self.GEMMA_MODEL if model_type == "gemma" else self.LITE_MODEL

        for attempt in range(5):
            try:
                response = self.client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                err_str = str(e).lower()
                is_retryable = any(x in err_str for x in ["503", "unavailable", "429", "rate limit", "overloaded"])
                
                if is_retryable and attempt < 4:
                    wait_time = 2 ** attempt
                    logger.warning(f"AI Service Busy ({model_id}, attempt {attempt+1}/5). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    if attempt >= 2 and model_type == "lite":
                        model_id = self.BACKUP_MODEL
                    continue

                logger.error(f"AI Text Generation Error (type={model_type}): {e}")
                return "Error generating response."
        return "Error generating response after multiple attempts."
