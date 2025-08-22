import pytest
import json
from unittest.mock import patch, AsyncMock

# Adjust path to import the app module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.flows.generation.enhanced_first_chapter import EnhancedChapterGenerator

# To mock the .content attribute of a LangChain AIMessage
class MockAIMessage:
    def __init__(self, content):
        self.content = content

@pytest.fixture
def generator():
    """Provides a fresh EnhancedChapterGenerator instance for each test."""
    return EnhancedChapterGenerator()

# Helper data with valid lengths
VALID_CHAPTER_TEXT = "This is a very long and detailed chapter designed specifically for testing. It needs to be well over one hundred characters to ensure that it successfully passes the length validation check that has been causing so many problems in the previous test runs."
VALID_CHOICE_TEXT = "This is a valid choice text because it is longer than ten characters."

def test_parse_and_validate_response_pure_json(generator: EnhancedChapterGenerator):
    """Test parsing a valid, pure JSON response."""
    response_data = {
        "chapter": VALID_CHAPTER_TEXT,
        "choices": [{"id": "choice_1", "text": VALID_CHOICE_TEXT, "consequence": "A consequence"}]
    }
    response_str = json.dumps(response_data)
    result = generator._parse_and_validate_response(response_str, 1)

    assert result["success"] is True
    assert result["chapter"] == response_data["chapter"]
    assert result["choices"][0]["text"] == VALID_CHOICE_TEXT

def test_parse_and_validate_response_hybrid_format(generator: EnhancedChapterGenerator):
    """Test parsing the hybrid format with a delimiter."""
    choices_data = {"choices": [{"id": 1, "text": VALID_CHOICE_TEXT, "consequence": "A consequence"}]}
    response_str = f"{VALID_CHAPTER_TEXT}\n### choices\n{json.dumps(choices_data)}"
    result = generator._parse_and_validate_response(response_str, 1)

    assert result["success"] is True
    assert result["chapter"] == VALID_CHAPTER_TEXT
    assert result["choices"][0]["text"] == VALID_CHOICE_TEXT

def test_parse_and_validate_response_invalid_json(generator: EnhancedChapterGenerator):
    response_str = '{"chapter": "content", "choices": [}'
    result = generator._parse_and_validate_response(response_str, 1)
    assert result["success"] is False
    assert "Invalid JSON" in result["error"]

def test_parse_and_validate_response_missing_fields(generator: EnhancedChapterGenerator):
    # Missing 'chapter'
    response_str = '{"choices": []}'
    result = generator._parse_and_validate_response(response_str, 1)
    assert result["success"] is False
    assert "Missing 'chapter' field" in result["error"]

    # Missing 'choices'
    response_str = f"{VALID_CHAPTER_TEXT} ### choices {{}}"
    result = generator._parse_and_validate_response(response_str, 1)
    assert result["success"] is False
    assert "No valid choices found" in result["error"]

@pytest.mark.asyncio
@patch('app.flows.generation.enhanced_first_chapter.chain')
async def test_generate_chapter_success(mock_chain, generator: EnhancedChapterGenerator):
    """Test the successful generation of a chapter."""
    response_data = {"chapter": VALID_CHAPTER_TEXT, "choices": [{"id": "c1", "text": VALID_CHOICE_TEXT}]}

    async def mock_ainvoke(*args, **kwargs):
        return MockAIMessage(content=json.dumps(response_data))

    mock_chain.ainvoke.side_effect = mock_ainvoke

    result = await generator.generate_chapter_from_outline("title", "outline")
    mock_chain.ainvoke.assert_called_once()
    assert result["success"] is True
    assert result["content"] == VALID_CHAPTER_TEXT

@pytest.mark.asyncio
@patch('app.flows.generation.enhanced_first_chapter.chain')
async def test_generate_chapter_retry_and_succeed(mock_chain, generator: EnhancedChapterGenerator):
    """Test that the generation retries on failure and then succeeds."""
    fail_response = MockAIMessage(content="this is not json")
    success_data = {"chapter": VALID_CHAPTER_TEXT, "choices": [{"id": 1, "text": VALID_CHOICE_TEXT}]}
    success_response = MockAIMessage(content=json.dumps(success_data))
    effects = [fail_response, success_response]

    async def mock_ainvoke(*args, **kwargs):
        return effects.pop(0)

    mock_chain.ainvoke.side_effect = mock_ainvoke

    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        result = await generator.generate_chapter_from_outline("title", "outline")
        assert result["success"] is True
        assert result["content"] == VALID_CHAPTER_TEXT
        assert mock_chain.ainvoke.call_count == 2
        mock_sleep.assert_called_once()

@pytest.mark.asyncio
@patch('app.flows.generation.enhanced_first_chapter.chain')
async def test_generate_chapter_max_retries_failed(mock_chain, generator: EnhancedChapterGenerator):
    """Test that the generation fails after all retries are exhausted."""
    fail_response = MockAIMessage(content="this is not json")

    async def mock_ainvoke(*args, **kwargs):
        return fail_response

    mock_chain.ainvoke.side_effect = mock_ainvoke

    result = await generator.generate_chapter_from_outline("title", "outline", max_retries=2)
    assert result["success"] is False
    assert "after 2 attempts" in result["content"]
    assert mock_chain.ainvoke.call_count == 2
