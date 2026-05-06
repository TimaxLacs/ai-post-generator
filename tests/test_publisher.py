import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from src.publisher import Publisher

@pytest.mark.asyncio
@patch("src.publisher.httpx.AsyncClient")
async def test_publish_to_tg_and_vk(mock_httpx):
    mock_client = AsyncMock()
    mock_httpx.return_value = mock_client
    
    # Mock TG successful response
    mock_tg_resp = MagicMock()
    mock_tg_resp.json.return_value = {"ok": True}
    
    # Mock VK successful response
    mock_vk_resp = MagicMock()
    mock_vk_resp.json.return_value = {"response": {"post_id": 123}}
    
    mock_client.post.side_effect = [mock_tg_resp, mock_vk_resp]
    
    publisher = Publisher(tg_token="test_tg", tg_chat="test_chat", vk_token="test_vk", vk_group="test_group")
    
    success = await publisher.publish("Test post [image: url] content")
    
    assert success is True
    # Verify TG call
    mock_client.post.assert_any_call(
        "https://api.telegram.org/bottest_tg/sendMessage",
        json={"chat_id": "test_chat", "text": "Test post content"}
    )
    # Verify VK call
    mock_client.post.assert_any_call(
        "https://api.vk.com/method/wall.post",
        data={
            "owner_id": "-test_group",
            "message": "Test post content",
            "access_token": "test_vk",
            "v": "5.131"
        }
    )

@pytest.mark.asyncio
@patch("src.publisher.httpx.AsyncClient")
async def test_publish_error_path(mock_httpx):
    mock_client = AsyncMock()
    mock_httpx.return_value = mock_client
    
    # Simulate an HTTP error for both requests
    mock_client.post.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
    
    publisher = Publisher(tg_token="test_tg", tg_chat="test_chat", vk_token="test_vk", vk_group="test_group")
    success = await publisher.publish("Test post content")
    
    assert success is False
    # Verify both calls were still attempted due to asyncio.gather
    assert mock_client.post.call_count == 2
