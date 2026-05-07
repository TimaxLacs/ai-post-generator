import logging
import json
import os
from src.publishers.base import BasePublisher
from src.config import settings

logger = logging.getLogger(__name__)

class TelegramPublisher(BasePublisher):
    name = "telegram"
    
    async def publish(self, text: str, images: list[str]) -> bool:
        if not settings.tg_bot_token or not settings.tg_channel_id:
            logger.error("Telegram credentials missing")
            return False
            
        if len(text) > 1024:
            caption = ""
            text_to_send_later = text
        else:
            caption = text
            text_to_send_later = ""

        res = None
        if not images:
            url = f"https://api.telegram.org/bot{settings.tg_bot_token}/sendMessage"
            payload = {"chat_id": settings.tg_channel_id, "text": text}
            res = await self.client.post(url, json=payload)
        elif len(images) == 1:
            url = f"https://api.telegram.org/bot{settings.tg_bot_token}/sendPhoto"
            with open(images[0], "rb") as f:
                files = {"photo": f}
                data = {"chat_id": settings.tg_channel_id, "caption": caption}
                res = await self.client.post(url, data=data, files=files)
        else:
            url = f"https://api.telegram.org/bot{settings.tg_bot_token}/sendMediaGroup"
            opened_files = []
            files = []
            media = []
            try:
                for i, img in enumerate(images):
                    f = open(img, "rb")
                    opened_files.append(f)
                    files.append((f"photo{i}", (os.path.basename(img), f, "image/jpeg")))
                    item = {"type": "photo", "media": f"attach://photo{i}"}
                    if i == 0 and caption:
                        item["caption"] = caption
                    media.append(item)
                
                data = {"chat_id": settings.tg_channel_id, "media": json.dumps(media)}
                res = await self.client.post(url, data=data, files=files)
            finally:
                for f in opened_files:
                    f.close()

        if res:
            res.raise_for_status()
            resp_data = res.json()
            if not resp_data.get("ok"):
                logger.error("Telegram API Error: %s", resp_data)
                return False

        if text_to_send_later:
            url = f"https://api.telegram.org/bot{settings.tg_bot_token}/sendMessage"
            payload = {"chat_id": settings.tg_channel_id, "text": text_to_send_later}
            res_text = await self.client.post(url, json=payload)
            res_text.raise_for_status()
            resp_data = res_text.json()
            if not resp_data.get("ok"):
                logger.error("Telegram API Error (sendMessage): %s", resp_data)
                return False

        return True
