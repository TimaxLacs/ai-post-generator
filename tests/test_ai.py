# tests/test_ai.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from openai import OpenAIError
from src.ai import AIPipeline
from src.config import settings

@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for tests."""
    original_api_key = settings.openrouter_api_key
    settings.openrouter_api_key = "test"
    yield
    settings.openrouter_api_key = original_api_key

@pytest.mark.asyncio
@patch("src.ai.AsyncOpenAI")
async def test_ai_pipeline_approved_first_try(mock_openai):
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_openai.return_value = mock_client
    
    # Use AsyncMock for the async method
    mock_client.chat.completions.create = AsyncMock()
    # Mock generator then moderator responses
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(content="Draft Post"))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="I think this is APPROVED. Great job!"))])
    ]
    
    pipeline = AIPipeline()
    status, final_text, feedback = await pipeline.process_block("Test Context")
    
    assert status is True
    assert final_text == "Draft Post"
    assert "APPROVED" in feedback.upper()
    
    await pipeline.close()
    mock_client.close.assert_awaited_once()

@pytest.mark.asyncio
@patch("src.ai.AsyncOpenAI")
async def test_ai_pipeline_rejected_three_times(mock_openai):
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
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
    
    pipeline = AIPipeline()
    status, final_text, feedback = await pipeline.process_block("Test Context")
    
    assert status is False
    assert final_text == "Draft 3"
    assert feedback == "Bad 3"
    
    await pipeline.close()
    mock_client.close.assert_awaited_once()

def test_ai_pipeline_missing_api_key():
    settings.openrouter_api_key = ""
    with pytest.raises(ValueError, match="API key must be provided in config"):
        AIPipeline()

@pytest.mark.asyncio
@patch("src.ai.AsyncOpenAI")
async def test_ai_pipeline_empty_context(mock_openai):
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_openai.return_value = mock_client

    pipeline = AIPipeline()
    with pytest.raises(ValueError, match="Context cannot be empty"):
        await pipeline.process_block("")
    
    with pytest.raises(ValueError, match="Context cannot be empty"):
        await pipeline.process_block("   ")
        
    await pipeline.close()

@pytest.mark.asyncio
@patch("src.ai.AsyncOpenAI")
async def test_ai_pipeline_openai_error_generation(mock_openai):
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_openai.return_value = mock_client
    
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.side_effect = OpenAIError("API is down")
    
    pipeline = AIPipeline()
    with pytest.raises(RuntimeError, match="Error during generation: API is down"):
        await pipeline.process_block("Test Context")
        
    await pipeline.close()

@pytest.mark.asyncio
@patch("src.ai.AsyncOpenAI")
async def test_ai_pipeline_openai_error_moderation(mock_openai):
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_openai.return_value = mock_client
    
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(content="Draft Post"))]),
        OpenAIError("API is down")
    ]
    
    pipeline = AIPipeline()
    with pytest.raises(RuntimeError, match="Error during moderation: API is down"):
        await pipeline.process_block("Test Context")
        
    await pipeline.close()
