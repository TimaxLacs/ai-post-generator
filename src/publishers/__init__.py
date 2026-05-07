import asyncio
import logging
import httpx
from src.publishers.telegram import TelegramPublisher
from src.publishers.vk import VKPublisher

logger = logging.getLogger(__name__)

class PublisherManager:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.publishers = [TelegramPublisher(self.client), VKPublisher(self.client)]
        
    async def close(self):
        await self.client.aclose()
        
    async def publish_all(self, text: str, images: list[str]) -> dict[str, bool]:
        tasks = [pub.publish(text, images) for pub in self.publishers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        outcome = {}
        for pub, result in zip(self.publishers, results):
            if isinstance(result, Exception):
                logger.error("Error in %s: %s", pub.name, result)
                outcome[pub.name] = False
            else:
                outcome[pub.name] = result
        return outcome
