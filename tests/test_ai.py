# tests/test_ai.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.ai import AIPipeline

@pytest.mark.asyncio
@patch("src.ai.AsyncOpenAI")
async def test_ai_pipeline_approved_first_try(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Use AsyncMock for the async method
    mock_client.chat.completions.create = AsyncMock()
    # Mock generator then moderator responses
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(content="Draft Post"))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="APPROVED"))])
    ]
    
    pipeline = AIPipeline(api_key="test")
    status, final_text, feedback = await pipeline.process_block("Test Context")
    
    assert status is True
    assert final_text == "Draft Post"
    assert feedback is None

@pytest.mark.asyncio
@patch("src.ai.AsyncOpenAI")
async def test_ai_pipeline_rejected_three_times(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Use AsyncMock for the async method
    mock_client.chat.completions.create = AsyncMock()
    # Mock generator -> moderator -> generator -> moderator -> generator -> moderator
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(content="Draft 1"))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="Bad 1"))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="Draft 2"))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="Bad 2"))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="Draft 3"))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="Bad 3"))])
    ]
    
    pipeline = AIPipeline(api_key="test")
    status, final_text, feedback = await pipeline.process_block("Test Context")
    
    assert status is False
    assert final_text == "Draft 3"
    assert feedback == "Bad 3"
