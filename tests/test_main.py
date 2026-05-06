import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import main

@pytest.mark.asyncio
@patch("main.StateManager")
@patch("main.AIPipeline")
@patch("main.Publisher")
async def test_main_success_flow(MockPub, MockAI, MockState):
    mock_state = MockState.return_value
    mock_ai = MockAI.return_value
    mock_pub = MockPub.return_value
    
    # Setup mock behavior
    mock_state.pop_next_block = AsyncMock(return_value="Test Context")
    mock_state.archive_block = AsyncMock()
    mock_ai.process_block = AsyncMock(return_value=(True, "Draft", None))
    mock_ai.close = AsyncMock()
    mock_pub.publish = AsyncMock(return_value=True)
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    mock_state.archive_block.assert_called_once_with("Test Context")
    mock_pub.publish.assert_called_once_with("Draft")

@pytest.mark.asyncio
@patch("main.StateManager")
@patch("main.AIPipeline")
@patch("main.Publisher")
async def test_main_failure_goes_to_next(MockPub, MockAI, MockState):
    mock_state = MockState.return_value
    mock_ai = MockAI.return_value
    mock_pub = MockPub.return_value
    
    # First block fails moderation, second block succeeds
    mock_state.pop_next_block = AsyncMock(side_effect=["Bad Context", "Good Context", None])
    mock_state.save_manual_review = AsyncMock()
    mock_state.archive_block = AsyncMock()
    mock_ai.process_block = AsyncMock(side_effect=[
        (False, "Bad Draft", "Bad"),
        (True, "Good Draft", None)
    ])
    mock_ai.close = AsyncMock()
    mock_pub.publish = AsyncMock(return_value=True)
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    mock_state.save_manual_review.assert_called_once_with("Bad Context", "Bad Draft", "Bad")
    mock_state.archive_block.assert_called_once_with("Good Context")
