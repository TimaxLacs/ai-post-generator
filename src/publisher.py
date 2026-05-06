import os
import re
import httpx
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class Publisher:
    def __init__(self, tg_token: Optional[str] = None, tg_chat: Optional[str] = None, vk_token: Optional[str] = None, vk_group: Optional[str] = None):
        self.tg_token = tg_token or os.getenv("TG_BOT_TOKEN")
        self.tg_chat = tg_chat or os.getenv("TG_CHANNEL_ID")
        self.vk_token = vk_token or os.getenv("VK_ACCESS_TOKEN")
        self.vk_group = vk_group or os.getenv("VK_GROUP_ID")
        self.client = httpx.AsyncClient()

    async def close(self):
        await self.client.aclose()

    def extract_images(self, text: str) -> tuple[str, list]:
        pattern = r"\[image:\s*(.+?)\]"
        images = re.findall(pattern, text)
        clean_text = re.sub(pattern, "", text).replace("  ", " ").strip()
        return clean_text, images

    async def publish_tg(self, text: str) -> bool:
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        payload = {"chat_id": self.tg_chat, "text": text}
        res = await self.client.post(url, json=payload)
        res.raise_for_status()
        return res.json().get("ok", False)

    async def publish_vk(self, text: str) -> bool:
        url = "https://api.vk.com/method/wall.post"
        payload = {
            "owner_id": f"-{self.vk_group}",
            "message": text,
            "access_token": self.vk_token,
            "v": "5.131"
        }
        res = await self.client.post(url, data=payload)
        res.raise_for_status()
        return "response" in res.json()

    async def publish(self, raw_text: str) -> bool:
        clean_text, images = self.extract_images(raw_text)
        
        results = await asyncio.gather(
            self.publish_tg(clean_text),
            self.publish_vk(clean_text),
            return_exceptions=True
        )
        
        tg_ok = False
        if isinstance(results[0], Exception):
            logger.error("Error occurred during TG publishing: %s", results[0])
        else:
            tg_ok = results[0]

        vk_ok = False
        if isinstance(results[1], Exception):
            logger.error("Error occurred during VK publishing: %s", results[1])
        else:
            vk_ok = results[1]
            
        return bool(tg_ok and vk_ok)
