import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Adjust path to import the app module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.dalle_service import DalleService, DalleAPIError

@pytest.fixture
def dalle_service():
    """Provides a fresh DalleService instance for each test."""
    return DalleService()

def create_async_mock_response(status, json_data=None, text_data=""):
    """Helper to create a mock aiohttp response object that is also an async context manager."""
    mock_response = AsyncMock()
    mock_response.status = status

    # The methods on the response object are awaitable
    mock_response.json = AsyncMock(return_value=json_data)
    mock_response.text = AsyncMock(return_value=text_data)

    # The response object itself is an async context manager
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__ = AsyncMock(return_value=None)

    return mock_response

@pytest.mark.asyncio
async def test_initialization(dalle_service: DalleService):
    """Test that the service initializes correctly."""
    assert dalle_service.api_key is not None
    assert "Authorization" in dalle_service.headers

@pytest.mark.asyncio
@patch('app.services.dalle_service.aiohttp.ClientSession')
async def test_generate_image_success(mock_session_cls, dalle_service: DalleService):
    """Test successful image generation."""
    mock_json_response = {
        "created": 1677652288,
        "data": [
            {
                "url": "http://example.com/image.png",
                "revised_prompt": "A cute cat playing with a ball of yarn, digital art."
            }
        ]
    }
    mock_response = create_async_mock_response(200, mock_json_response)

    mock_session = mock_session_cls.return_value.__aenter__.return_value
    mock_session.post = MagicMock(return_value=mock_response)

    prompt = "A cute cat"
    result = await dalle_service.generate_image(prompt, size="1024x1024")

    assert result["status"] == "completed"
    assert result["primary_image_url"] == "http://example.com/image.png"
    assert result["revised_prompt"] == "A cute cat playing with a ball of yarn, digital art."
    assert result["image_width"] == 1024

    mock_session.post.assert_called_once()
    called_payload = mock_session.post.call_args.kwargs['json']
    assert called_payload['prompt'] == prompt
    assert called_payload['size'] == '1024x1024'

@pytest.mark.asyncio
@patch('app.services.dalle_service.aiohttp.ClientSession')
async def test_generate_image_api_error(mock_session_cls, dalle_service: DalleService):
    """Test handling of a non-200 API error."""
    mock_response = create_async_mock_response(500, text_data="Internal Server Error")

    mock_session = mock_session_cls.return_value.__aenter__.return_value
    mock_session.post = MagicMock(return_value=mock_response)

    with pytest.raises(DalleAPIError, match="API request failed: 500 - Internal Server Error"):
        await dalle_service.generate_image("a prompt that will fail")

@pytest.mark.asyncio
@patch('app.services.dalle_service.aiohttp.ClientSession')
async def test_generate_image_rate_limit_retry(mock_session_cls, dalle_service: DalleService):
    """Test the retry logic on a 429 rate limit error."""
    rate_limit_response = create_async_mock_response(429, text_data="Rate limit exceeded")

    success_json = {
        "data": [{"url": "http://example.com/image.png", "revised_prompt": "Success"}]
    }
    success_response = create_async_mock_response(200, success_json)

    mock_session = mock_session_cls.return_value.__aenter__.return_value
    mock_session.post = MagicMock(side_effect=[rate_limit_response, success_response])

    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        result = await dalle_service.generate_image("a prompt")
        assert result["status"] == "completed"
        assert mock_session.post.call_count == 2
        mock_sleep.assert_called_once()

def test_enhance_prompt_for_text(dalle_service: DalleService):
    """Test the internal prompt enhancement logic."""
    base_prompt = "A fantasy landscape"
    title = "The Lost Artifact"
    author = "J.R.R. Tolkien"

    enhanced = dalle_service._enhance_prompt_for_text(base_prompt, title, author)

    assert base_prompt in enhanced
    assert "large readable title 'The Lost Artifact' at the top" in enhanced
    assert "author name 'By J.R.R. Tolkien' at the bottom" in enhanced

    enhanced_no_author = dalle_service._enhance_prompt_for_text(base_prompt, title)
    assert "author name" not in enhanced_no_author
