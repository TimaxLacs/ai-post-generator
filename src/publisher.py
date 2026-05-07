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

    async def publish_tg(self, text: str, images: list[str]) -> bool:
        if images:
            url = f"https://api.telegram.org/bot{self.tg_token}/sendPhoto"
            with open(images[0], "rb") as f:
                files = {"photo": f}
                data = {"chat_id": self.tg_chat, "caption": text}
                res = await self.client.post(url, data=data, files=files)
        else:
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            payload = {"chat_id": self.tg_chat, "text": text}
            res = await self.client.post(url, json=payload)
            
        res.raise_for_status()
        resp_data = res.json()
        if not resp_data.get("ok"):
            logger.error("Telegram API Error: %s", resp_data)
        return resp_data.get("ok", False)

    async def _upload_vk_photo(self, image_path: str) -> Optional[str]:
        # 1. Get upload server
        url = "https://api.vk.com/method/photos.getWallUploadServer"
        payload = {
            "group_id": self.vk_group,
            "access_token": self.vk_token,
            "v": "5.131"
        }
        res = await self.client.post(url, data=payload)
        res.raise_for_status()
        
        response_data = res.json()
        if "error" in response_data:
            raise Exception(f"VK API Error (getWallUploadServer): {response_data['error']}")
            
        upload_url = response_data["response"]["upload_url"]

        # 2. Upload photo
        with open(image_path, "rb") as f:
            files = {"photo": f}
            res = await self.client.post(upload_url, files=files)
            res.raise_for_status()
            upload_data = res.json()
            
        if not upload_data.get("photo") or upload_data.get("photo") == "[]":
            raise Exception("VK API Error: Uploaded photo is empty")

        # 3. Save photo
        url = "https://api.vk.com/method/photos.saveWallPhoto"
        save_payload = {
            "group_id": self.vk_group,
            "server": upload_data["server"],
            "photo": upload_data["photo"],
            "hash": upload_data["hash"],
            "access_token": self.vk_token,
            "v": "5.131"
        }
        res = await self.client.post(url, data=save_payload)
        res.raise_for_status()
        
        save_data = res.json()
        if "error" in save_data:
            raise Exception(f"VK API Error (saveWallPhoto): {save_data['error']}")
            
        saved_photo = save_data["response"][0]
        return f"photo{saved_photo['owner_id']}_{saved_photo['id']}"

    async def publish_vk(self, text: str, images: list[str]) -> bool:
        attachments = []
        if images:
            att = await self._upload_vk_photo(images[0])
            if att:
                attachments.append(att)

        url = "https://api.vk.com/method/wall.post"
        payload = {
            "owner_id": f"-{self.vk_group}",
            "message": text,
            "access_token": self.vk_token,
            "v": "5.131"
        }
        if attachments:
            payload["attachments"] = ",".join(attachments)

        res = await self.client.post(url, data=payload)
        res.raise_for_status()
        
        resp_data = res.json()
        if "error" in resp_data:
            logger.error("VK API Error (wall.post): %s", resp_data["error"])
            return False
        return "response" in resp_data

    async def publish(self, raw_text: str) -> bool:
        clean_text, images = self.extract_images(raw_text)
        
        results = await asyncio.gather(
            self.publish_tg(clean_text, images),
            self.publish_vk(clean_text, images),
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
