import os
import re
import httpx
import logging

logger = logging.getLogger(__name__)

class Publisher:
    def __init__(self, tg_token=None, tg_chat=None, vk_token=None, vk_group=None):
        self.tg_token = tg_token or os.getenv("TG_BOT_TOKEN")
        self.tg_chat = tg_chat or os.getenv("TG_CHANNEL_ID")
        self.vk_token = vk_token or os.getenv("VK_ACCESS_TOKEN")
        self.vk_group = vk_group or os.getenv("VK_GROUP_ID")

    def extract_images(self, text: str) -> tuple[str, list]:
        pattern = r"\[image:\s*(.+?)\]"
        images = re.findall(pattern, text)
        clean_text = re.sub(pattern, "", text).strip()
        return clean_text, images

    async def publish_tg(self, text: str) -> bool:
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        payload = {"chat_id": self.tg_chat, "text": text}
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload)
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
        async with httpx.AsyncClient() as client:
            res = await client.post(url, data=payload)
            res.raise_for_status()
            return "response" in res.json()

    async def publish(self, raw_text: str) -> bool:
        clean_text, images = self.extract_images(raw_text)
        # Note: Image uploading logic to VK/TG is omitted here for simplicity, 
        # it requires multipart forms and VK specific photo upload flows. 
        # We start with text publishing.
        
        try:
            tg_ok = await self.publish_tg(clean_text)
            vk_ok = await self.publish_vk(clean_text)
            return tg_ok and vk_ok
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error occurred during publishing: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error during publishing: %s", e)
            return False
