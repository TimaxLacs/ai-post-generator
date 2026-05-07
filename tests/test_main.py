import pytest
from unittest.mock import patch, AsyncMock
import main

@pytest.mark.asyncio
@patch("main.asyncio.sleep", new_callable=AsyncMock)
@patch("main.init_db", new_callable=AsyncMock)
@patch("main.ingest_markdown", new_callable=AsyncMock)
@patch("main.get_next_pending_post", new_callable=AsyncMock)
@patch("main.update_post_state", new_callable=AsyncMock)
@patch("main.AIPipeline")
@patch("main.PublisherManager")
async def test_main_success_flow(MockPubManager, MockAI, mock_update_post_state, mock_get_next, mock_ingest, mock_init, mock_sleep):
    mock_ai = MockAI.return_value
    mock_pub = MockPubManager.return_value
    
    # Setup mock behavior
    mock_get_next.side_effect = [
        {"id": 1, "context": "Test Context [image: images/pic.png]"},
        {"id": 2, "context": "Second Context"},
        None
    ]
    
    mock_ai.process_block = AsyncMock(side_effect=[(True, "Draft 1", None), (True, "Draft 2", None)])
    mock_ai.close = AsyncMock()
    mock_pub.publish_all = AsyncMock(return_value={"telegram": True, "vk": True})
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    assert mock_init.call_count == 1
    assert mock_ingest.call_count == 1
    assert mock_ai.process_block.call_count == 2
    assert mock_pub.publish_all.call_count == 2
    
    # Check update_post_state calls for the first post
    # generating -> publishing -> published
    assert mock_update_post_state.call_args_list[0][0] == ("queue.db", 1)
    assert mock_update_post_state.call_args_list[0][1]["status"] == "generating"
    
    assert mock_update_post_state.call_args_list[1][0] == ("queue.db", 1)
    assert mock_update_post_state.call_args_list[1][1]["status"] == "publishing"
    
    assert mock_update_post_state.call_args_list[2][0] == ("queue.db", 1)
    assert mock_update_post_state.call_args_list[2][1]["status"] == "published"
    assert mock_update_post_state.call_args_list[2][1]["tg_ok"] is True
    assert mock_update_post_state.call_args_list[2][1]["vk_ok"] is True


@pytest.mark.asyncio
@patch("main.asyncio.sleep", new_callable=AsyncMock)
@patch("main.init_db", new_callable=AsyncMock)
@patch("main.ingest_markdown", new_callable=AsyncMock)
@patch("main.get_next_pending_post", new_callable=AsyncMock)
@patch("main.update_post_state", new_callable=AsyncMock)
@patch("main.AIPipeline")
@patch("main.PublisherManager")
async def test_main_failure_goes_to_next(MockPubManager, MockAI, mock_update_post_state, mock_get_next, mock_ingest, mock_init, mock_sleep):
    mock_ai = MockAI.return_value
    mock_pub = MockPubManager.return_value
    
    # First block fails moderation, second block succeeds
    mock_get_next.side_effect = [
        {"id": 1, "context": "Bad Context"},
        {"id": 2, "context": "Good Context"},
        None
    ]
    
    mock_ai.process_block = AsyncMock(side_effect=[
        (False, "Bad Draft", "Bad"),
        (True, "Good Draft", None)
    ])
    mock_ai.close = AsyncMock()
    mock_pub.publish_all = AsyncMock(return_value={"telegram": True, "vk": True})
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    
    # Post 1 should be set to manual_review
    # Post 1 generating -> manual_review
    assert mock_update_post_state.call_args_list[0][0] == ("queue.db", 1)
    assert mock_update_post_state.call_args_list[0][1]["status"] == "generating"
    
    assert mock_update_post_state.call_args_list[1][0] == ("queue.db", 1)
    assert mock_update_post_state.call_args_list[1][1]["status"] == "manual_review"
    assert mock_update_post_state.call_args_list[1][1]["feedback"] == "Bad"


@pytest.mark.asyncio
@patch("main.asyncio.sleep", new_callable=AsyncMock)
@patch("main.init_db", new_callable=AsyncMock)
@patch("main.ingest_markdown", new_callable=AsyncMock)
@patch("main.get_next_pending_post", new_callable=AsyncMock)
@patch("main.update_post_state", new_callable=AsyncMock)
@patch("main.AIPipeline")
@patch("main.PublisherManager")
async def test_main_publish_partial_and_full_failure(MockPubManager, MockAI, mock_update_post_state, mock_get_next, mock_ingest, mock_init, mock_sleep):
    mock_ai = MockAI.return_value
    mock_pub = MockPubManager.return_value
    
    # First block fails publishing entirely, second block partially fails
    mock_get_next.side_effect = [
        {"id": 1, "context": "Fail Context"},
        {"id": 2, "context": "Partial Context"},
        None
    ]
    
    mock_ai.process_block = AsyncMock(side_effect=[
        (True, "Fail Draft", None),
        (True, "Partial Draft", None)
    ])
    mock_ai.close = AsyncMock()
    mock_pub.publish_all = AsyncMock(side_effect=[
        {"telegram": False, "vk": False},
        {"telegram": True, "vk": False}
    ])
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    
    # Post 1: generating -> publishing -> failed
    assert mock_update_post_state.call_args_list[2][0] == ("queue.db", 1)
    assert mock_update_post_state.call_args_list[2][1]["status"] == "failed"
    assert mock_update_post_state.call_args_list[2][1]["feedback"] == "Complete API Publishing Error"
    
    # Post 2: generating -> publishing -> partial_failure
    assert mock_update_post_state.call_args_list[5][0] == ("queue.db", 2)
    assert mock_update_post_state.call_args_list[5][1]["status"] == "partial_failure"
    assert mock_update_post_state.call_args_list[5][1]["tg_ok"] is True
    assert mock_update_post_state.call_args_list[5][1]["vk_ok"] is False


@pytest.mark.asyncio
@patch("main.asyncio.sleep", new_callable=AsyncMock)
@patch("main.init_db", new_callable=AsyncMock)
@patch("main.ingest_markdown", new_callable=AsyncMock)
@patch("main.get_next_pending_post", new_callable=AsyncMock)
@patch("main.update_post_state", new_callable=AsyncMock)
@patch("main.AIPipeline")
@patch("main.PublisherManager")
async def test_main_exception_handling(MockPubManager, MockAI, mock_update_post_state, mock_get_next, mock_ingest, mock_init, mock_sleep):
    mock_ai = MockAI.return_value
    mock_pub = MockPubManager.return_value
    
    # First block throws exception, second block succeeds
    mock_get_next.side_effect = [
        {"id": 1, "context": "Error Context"},
        {"id": 2, "context": "Good Context"},
        None
    ]
    
    # Process block raises exception for first context
    mock_ai.process_block = AsyncMock(side_effect=[
        Exception("Simulated AI error"),
        (True, "Good Draft", None)
    ])
    mock_ai.close = AsyncMock()
    mock_pub.publish_all = AsyncMock(return_value={"telegram": True, "vk": True})
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    
    # Post 1: generating -> failed (due to exception)
    assert mock_update_post_state.call_args_list[1][0] == ("queue.db", 1)
    assert mock_update_post_state.call_args_list[1][1]["status"] == "failed"
    assert "Simulated AI error" in mock_update_post_state.call_args_list[1][1]["feedback"]
