import asyncio
import logging
from typing import Any, Dict, List

import httpx
from sqlalchemy.orm import Session

from app.agents.execution_agent import ExecutionAgent
from app.core.config import settings
from app.core.db import SessionLocal

logger = logging.getLogger(__name__)


class TelegramPollingService:
    def __init__(self) -> None:
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset = 0
        self.agent = ExecutionAgent()

    async def get_updates(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        try:
            params = {"offset": self.offset, "timeout": 30}
            resp = await client.get(f"{self.base_url}/getUpdates", params=params)
            if resp.status_code != 200:
                logger.error(f"Telegram API error: {resp.status_code} - {resp.text}")
                return []
            
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"Telegram API error: {data}")
                return []
            
            return data.get("result", [])
        except Exception as e:
            logger.error(f"Exception during getUpdates: {e}")
            return []

    async def run(self) -> None:
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Polling service disabled.")
            return

        logger.info("Starting Telegram Polling service...")
        async with httpx.AsyncClient(timeout=40) as client:
            while True:
                updates = await self.get_updates(client)
                for update in updates:
                    update_id = update.get("update_id")
                    if update_id:
                        self.offset = update_id + 1
                    
                    # Process current update
                    db = SessionLocal()
                    try:
                        await self.agent.handle_update(update=update, db=db)
                    except Exception as e:
                        logger.error(f"Error handling Telegram update: {e}")
                    finally:
                        db.close()
                
                await asyncio.sleep(1)


async def start_polling() -> None:
    service = TelegramPollingService()
    await service.run()
