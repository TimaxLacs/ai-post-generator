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
    mock_state.pop_next_block = AsyncMock(return_value="Test Context [image: pic.png]")
    mock_state.archive_block = AsyncMock()
    mock_ai.process_block = AsyncMock(return_value=(True, "Draft", None))
    mock_ai.close = AsyncMock()
    mock_pub.publish = AsyncMock(return_value=True)
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    mock_ai.process_block.assert_called_once_with("Test Context")
    mock_state.archive_block.assert_called_once_with("Test Context [image: pic.png]")
    mock_pub.publish.assert_called_once_with("Draft", ["pic.png"])

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

@pytest.mark.asyncio
@patch("main.StateManager")
@patch("main.AIPipeline")
@patch("main.Publisher")
async def test_main_publish_failure(MockPub, MockAI, MockState):
    mock_state = MockState.return_value
    mock_ai = MockAI.return_value
    mock_pub = MockPub.return_value
    
    # First block fails publishing, second block succeeds
    mock_state.pop_next_block = AsyncMock(side_effect=["Fail Context", "Good Context", None])
    mock_state.save_manual_review = AsyncMock()
    mock_state.archive_block = AsyncMock()
    mock_ai.process_block = AsyncMock(side_effect=[
        (True, "Fail Draft", None),
        (True, "Good Draft", None)
    ])
    mock_ai.close = AsyncMock()
    mock_pub.publish = AsyncMock(side_effect=[False, True])
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    mock_state.save_manual_review.assert_called_once_with("Fail Context", "Fail Draft", "API Publishing Error")
    mock_state.archive_block.assert_called_once_with("Good Context")

@pytest.mark.asyncio
@patch("main.StateManager")
@patch("main.AIPipeline")
@patch("main.Publisher")
async def test_main_exception_handling(MockPub, MockAI, MockState):
    mock_state = MockState.return_value
    mock_ai = MockAI.return_value
    mock_pub = MockPub.return_value
    
    # First block throws exception, second block succeeds
    mock_state.pop_next_block = AsyncMock(side_effect=["Error Context", "Good Context", None])
    mock_state.save_manual_review = AsyncMock()
    mock_state.archive_block = AsyncMock()
    
    # Process block raises exception for first context
    mock_ai.process_block = AsyncMock(side_effect=[
        Exception("Simulated AI error"),
        (True, "Good Draft", None)
    ])
    mock_ai.close = AsyncMock()
    mock_pub.publish = AsyncMock(return_value=True)
    mock_pub.close = AsyncMock()
    
    result = await main.run()
    
    assert result is True
    mock_state.save_manual_review.assert_called_once_with("Error Context", "", "Processing Error: Simulated AI error")
    mock_state.archive_block.assert_called_once_with("Good Context")
