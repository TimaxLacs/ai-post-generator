import logging
from typing import Optional
from src.publishers.base import BasePublisher
from src.config import settings

logger = logging.getLogger(__name__)

class VKPublisher(BasePublisher):
    name = "vk"
    
    async def _upload_vk_photo(self, image_path: str) -> Optional[str]:
        url = "https://api.vk.com/method/photos.getWallUploadServer"
        payload = {"group_id": settings.vk_group_id, "access_token": settings.vk_access_token, "v": "5.131"}
        res = await self.client.post(url, data=payload)
        res.raise_for_status()
        response_data = res.json()
        if "error" in response_data:
            raise Exception(f"VK API Error (getWallUploadServer): {response_data['error']}")
            
        upload_url = response_data["response"]["upload_url"]

        with open(image_path, "rb") as f:
            files = {"photo": f}
            res = await self.client.post(upload_url, files=files)
            res.raise_for_status()
            upload_data = res.json()
            
        if not upload_data.get("photo") or upload_data.get("photo") == "[]":
            raise Exception("VK API Error: Uploaded photo is empty")

        url = "https://api.vk.com/method/photos.saveWallPhoto"
        save_payload = {
            "group_id": settings.vk_group_id,
            "server": upload_data["server"],
            "photo": upload_data["photo"],
            "hash": upload_data["hash"],
            "access_token": settings.vk_access_token,
            "v": "5.131"
        }
        res = await self.client.post(url, data=save_payload)
        res.raise_for_status()
        
        save_data = res.json()
        if "error" in save_data:
            raise Exception(f"VK API Error (saveWallPhoto): {save_data['error']}")
            
        saved_photo = save_data["response"][0]
        return f"photo{saved_photo['owner_id']}_{saved_photo['id']}"

    async def publish(self, text: str, images: list[str]) -> bool:
        if not settings.vk_access_token or not settings.vk_group_id:
            logger.error("VK credentials missing")
            return False
            
        attachments = []
        for img in images:
            att = await self._upload_vk_photo(img)
            if att:
                attachments.append(att)

        url = "https://api.vk.com/method/wall.post"
        payload = {
            "owner_id": f"-{settings.vk_group_id}",
            "message": text,
            "access_token": settings.vk_access_token,
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
