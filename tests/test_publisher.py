import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from src.publisher import Publisher

@pytest.mark.asyncio
@patch("src.publisher.httpx.AsyncClient")
@patch("builtins.open", new_callable=mock_open, read_data=b"dummy_image_data")
async def test_publish_to_tg_and_vk(mock_file, mock_httpx):
    mock_client = AsyncMock()
    mock_httpx.return_value = mock_client
    
    # Mock TG successful response
    mock_tg_resp = MagicMock()
    mock_tg_resp.json.return_value = {"ok": True}
    
    # Mock VK successful responses
    mock_vk_server_resp = MagicMock()
    mock_vk_server_resp.json.return_value = {"response": {"upload_url": "http://vk.com/upload"}}
    
    mock_vk_upload_resp = MagicMock()
    mock_vk_upload_resp.json.return_value = {"server": 1, "photo": "xyz", "hash": "abc"}
    
    mock_vk_save_resp = MagicMock()
    mock_vk_save_resp.json.return_value = {"response": [{"id": 456, "owner_id": 123}]}
    
    mock_vk_post_resp = MagicMock()
    mock_vk_post_resp.json.return_value = {"response": {"post_id": 789}}
    
    async def mock_post(url, *args, **kwargs):
        if "telegram.org" in url:
            return mock_tg_resp
        elif "getWallUploadServer" in url:
            return mock_vk_server_resp
        elif "vk.com/upload" in url:
            return mock_vk_upload_resp
        elif "saveWallPhoto" in url:
            return mock_vk_save_resp
        elif "wall.post" in url:
            return mock_vk_post_resp
        raise ValueError(f"Unexpected url: {url}")

    mock_client.post.side_effect = mock_post
    
    publisher = Publisher(tg_token="test_tg", tg_chat="test_chat", vk_token="test_vk", vk_group="test_group")
    
    success = await publisher.publish("Test post [image: url] content")
    
    assert success is True
    # Verify TG call with photo
    mock_client.post.assert_any_call(
        "https://api.telegram.org/bottest_tg/sendPhoto",
        data={"chat_id": "test_chat", "caption": "Test post content"},
        files={"photo": mock_file()}
    )
    # Verify VK call with attachments
    mock_client.post.assert_any_call(
        "https://api.vk.com/method/wall.post",
        data={
            "owner_id": "-test_group",
            "message": "Test post content",
            "access_token": "test_vk",
            "v": "5.131",
            "attachments": "photo123_456"
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
    success = await publisher.publish("Test post content") # No image for this test
    
    assert success is False
    # Verify both calls were still attempted due to asyncio.gather
    assert mock_client.post.call_count == 2
