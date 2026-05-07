import httpx
from abc import ABC, abstractmethod

class BasePublisher(ABC):
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    async def publish(self, text: str, images: list[str]) -> bool:
        pass
