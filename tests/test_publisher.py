import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.publisher import Publisher

@pytest.mark.asyncio
@patch("src.publisher.httpx.AsyncClient")
async def test_publish_to_tg_and_vk(mock_httpx):
    mock_client = AsyncMock()
    mock_httpx.return_value.__aenter__.return_value = mock_client
    
    # Mock TG successful response
    mock_tg_resp = MagicMock()
    mock_tg_resp.json.return_value = {"ok": True}
    
    # Mock VK successful response
    mock_vk_resp = MagicMock()
    mock_vk_resp.json.return_value = {"response": {"post_id": 123}}
    
    mock_client.post.side_effect = [mock_tg_resp, mock_vk_resp]
    
    publisher = Publisher(tg_token="test_tg", tg_chat="test_chat", vk_token="test_vk", vk_group="test_group")
    
    # We test without images for simplicity in unit tests
    success = await publisher.publish("Test post content")
    
    assert success is True
    # Verify TG call
    mock_client.post.assert_any_call(
        "https://api.telegram.org/bottest_tg/sendMessage",
        json={"chat_id": "test_chat", "text": "Test post content"}
    )
