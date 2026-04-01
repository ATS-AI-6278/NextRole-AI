import re
import json
import logging
import asyncio
from typing import Any, Dict, Optional

from google import genai
from app.core.config import settings

import time
logger = logging.getLogger(__name__)


class GemmaThrottle:
    def __init__(self, tpm_limit: int = 15000, rpm_limit: int = 15):
        self.tpm_limit = tpm_limit
        self.rpm_limit = rpm_limit
        self.requests = []  # List of (timestamp, token_count)
        self.lock = asyncio.Lock()

    async def wait_for_quota(self, token_estimate: int):
        async with self.lock:
            while True:
                now = time.time()
                # 1. Purge requests older than 60 seconds
                self.requests = [r for r in self.requests if now - r[0] < 60]
                
                # 2. Check TPM and RPM
                current_tpm = sum(r[1] for r in self.requests)
                current_rpm = len(self.requests)
                
                if current_tpm + token_estimate <= self.tpm_limit and current_rpm + 1 <= self.rpm_limit:
                    # Within quota!
                    self.requests.append((now, token_estimate))
                    return
                
                # 3. Wait until the oldest request falls out of the window
                if self.requests:
                    wait_sec = 60 - (now - self.requests[0][0]) + 0.1
                    logger.info(f"Gemma Quota Exceeded (TPM={current_tpm}/{self.tpm_limit}, RPM={current_rpm}/{self.rpm_limit}). Waiting {wait_sec:.1f}s...")
                    await asyncio.sleep(max(wait_sec, 1))
                else:
                    # Should not happen if within limits, but fallback:
                    await asyncio.sleep(1)


class AIClient:
    def __init__(self):
        self.gemma_throttle = GemmaThrottle()
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not set. AI capabilities will be disabled.")
            self.client = None
        else:
            # Strictly using the new SDK
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            # User specified models - Strictly using these two primary models
            self.LITE_MODEL = "gemini-3.1-flash-lite-preview"
            self.GEMMA_MODEL = "gemma-3-12b-it"
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

                if model_type == "gemma":
                    # 1 token approx 3 characters (conservative buffer for Gemma)
                    token_estimate = len(prompt) // 3 + 100 
                    await self.gemma_throttle.wait_for_quota(token_estimate)

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
                if model_type == "gemma":
                    token_estimate = len(prompt) // 3 + 100
                    await self.gemma_throttle.wait_for_quota(token_estimate)

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
