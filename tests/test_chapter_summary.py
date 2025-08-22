import pytest
import json
from unittest.mock import patch, MagicMock

# Adjust path to import the app module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.chapter_summary import EnhancedChapterSummarizer

@pytest.fixture
def summarizer_instance():
    """Provides a fresh, unmocked EnhancedChapterSummarizer instance for direct testing."""
    return EnhancedChapterSummarizer()

def test_validate_summary_quality(summarizer_instance: EnhancedChapterSummarizer):
    """Test the internal summary quality validation logic."""
    long_content = "word " * 500

    # Test with a good, long summary that meets all criteria
    good_summary = "character emotion conflict setting dialogue relationship motivation consequence decision will future later affects " * 30
    score = summarizer_instance._validate_summary_quality(long_content, good_summary)
    assert score >= 9

    # Test with a short summary
    short_summary = "A short summary."
    score = summarizer_instance._validate_summary_quality(long_content, short_summary)
    assert score < 5

@patch('app.services.chapter_summary.OpenAI')
def test_create_detailed_summary_success(mock_openai_cls):
    """Test the successful creation of a detailed summary."""
    # Instantiate inside the test where the patch is active
    summarizer = EnhancedChapterSummarizer()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This is a detailed and high-quality summary."
    mock_openai_instance = mock_openai_cls.return_value
    mock_openai_instance.chat.completions.create.return_value = mock_response

    result = summarizer.create_detailed_summary(
        chapter_content="A long chapter content goes here.",
        chapter_number=1
    )

    mock_openai_instance.chat.completions.create.assert_called_once()
    assert result["success"] is True
    assert result["summary"] == "This is a detailed and high-quality summary."

@patch('app.services.chapter_summary.OpenAI')
def test_create_detailed_summary_failure(mock_openai_cls):
    """Test the summary creation when the OpenAI API call fails."""
    summarizer = EnhancedChapterSummarizer()

    mock_openai_instance = mock_openai_cls.return_value
    mock_openai_instance.chat.completions.create.side_effect = Exception("API Error")

    result = summarizer.create_detailed_summary(
        chapter_content="A chapter.",
        chapter_number=1
    )

    assert result["success"] is False
    assert "API Error" in result["error"]

@patch('app.services.chapter_summary.OpenAI')
def test_extract_story_elements_success(mock_openai_cls):
    """Test the successful extraction of structured story elements."""
    summarizer = EnhancedChapterSummarizer()

    mock_elements = {
        "characters": [{"name": "John"}],
        "plot_threads": [{"thread_name": "Find the amulet"}]
    }
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(mock_elements)

    mock_openai_instance = mock_openai_cls.return_value
    mock_openai_instance.chat.completions.create.return_value = mock_response

    result = summarizer.extract_story_elements(
        chapter_content="Some content.",
        chapter_number=1
    )

    assert result["success"] is True
    assert len(result["story_elements"]["characters"]) == 1
    assert result["story_elements"]["characters"][0]["name"] == "John"

@patch('app.services.chapter_summary.OpenAI')
def test_extract_story_elements_invalid_json(mock_openai_cls):
    """Test element extraction when the LLM returns invalid JSON."""
    summarizer = EnhancedChapterSummarizer()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This is not valid JSON"

    mock_openai_instance = mock_openai_cls.return_value
    mock_openai_instance.chat.completions.create.return_value = mock_response

    result = summarizer.extract_story_elements(
        chapter_content="Some content.",
        chapter_number=1
    )

    assert result["success"] is False
    assert "Expecting value" in result["error"]
