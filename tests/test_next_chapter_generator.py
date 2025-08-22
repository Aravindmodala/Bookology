import pytest
import json
from unittest.mock import patch, MagicMock

# Adjust path to import the app module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.flows.generation.next_chapter_generator import BestsellerChapterGenerator, QualityMetrics

@pytest.fixture
def chapter_generator():
    """Provides a fresh BestsellerChapterGenerator instance for each test."""
    # We patch the LLM instances at the point of use within the tests
    return BestsellerChapterGenerator()

# A sample valid LLM response for generating a chapter
SAMPLE_LLM_RESPONSE = {
    "chapter": "The hero faced the dragon bravely. It was a mighty beast, with scales of obsidian and eyes of fire.",
    "choices": [
        {"id": "choice_1", "title": "Attack the dragon", "description": "A frontal assault.", "story_impact": "High risk, high reward.", "choice_type": "action"},
        {"id": "choice_2", "title": "Sneak past", "description": "A stealthy approach.", "story_impact": "Lower risk, but the dragon remains.", "choice_type": "strategic"}
    ]
}

# To mock the .content attribute of a LangChain AIMessage
class MockAIMessage:
    def __init__(self, content):
        self.content = content

@pytest.mark.asyncio
@patch('app.flows.generation.next_chapter_generator.llm')
async def test_mock_setup_is_working(mock_llm, chapter_generator: BestsellerChapterGenerator):
    """
    A simple test to confirm that the mock setup for the langchain LLM is working.
    """
    # Configure the mock for the base_chain
    mock_llm_response_content = json.dumps(SAMPLE_LLM_RESPONSE)
    mock_ai_message = MockAIMessage(content=mock_llm_response_content)

    # The chain call will eventually call the llm's invoke method
    # Since the chain is `prompt | llm`, we mock the llm's return value from invoke
    # The BestsellerChapterGenerator wraps the llm in a chain, so we patch the llm instance
    # that the chain uses.

    # We need to mock the chain object within the generator instance
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_ai_message
    chapter_generator.base_chain = mock_chain

    # Call the method that uses the chain
    result = chapter_generator._generate_single_version(
        story_title="Test Story",
        next_chapter_title="The Next Step",
        story_outline="An outline.",
        story_dna_context="Some DNA.",
        chapter_number=1,
        user_choice="",
        is_game_mode=False
    )

    # Assert that our mocked chain was used
    mock_chain.invoke.assert_called_once()
    assert result is not None
    assert result.content == SAMPLE_LLM_RESPONSE["chapter"]

def test_validate_dna_quality(chapter_generator: BestsellerChapterGenerator):
    """Test the _validate_dna_quality helper method."""
    # Test with good DNA
    good_dna = [
        "Character A is a cheerful optimist who always looks on the bright side.",
        "Plot point B is that the magical amulet was found in the ancient tomb.",
        "Location C is a bustling city with towering spires and flying vehicles.",
        "Relationship D: Character A and Character B are close friends and allies."
    ]
    result = chapter_generator._validate_dna_quality(good_dna)
    assert result["is_valid"] is True
    assert not result["issues"]

    # Test with empty DNA
    empty_dna = ["", "  "]
    result = chapter_generator._validate_dna_quality(empty_dna)
    assert result["is_valid"] is False
    assert "mostly_empty" in result["issues"]

    # Test with fallback flags
    fallback_dna = ["This is a fallback context."]
    result = chapter_generator._validate_dna_quality(fallback_dna)
    assert result["is_valid"] is False
    assert "fallback_flagged" in result["issues"]

def test_parse_chapter_response(chapter_generator: BestsellerChapterGenerator):
    """Test the _parse_chapter_response helper method."""
    # Test with perfect JSON
    good_json_str = json.dumps(SAMPLE_LLM_RESPONSE)
    result = chapter_generator._parse_chapter_response(good_json_str, 1)
    assert result["success"] is True
    assert result["chapter_content"] == SAMPLE_LLM_RESPONSE["chapter"]
    assert len(result["choices"]) == 2

    # Test with markdown block
    md_json_str = f"```json\n{good_json_str}\n```"
    result = chapter_generator._parse_chapter_response(md_json_str, 1)
    assert result["success"] is True
    assert result["chapter_content"] == SAMPLE_LLM_RESPONSE["chapter"]

    # Test with invalid JSON
    bad_json_str = '{"chapter": "content", "choices": [}'
    result = chapter_generator._parse_chapter_response(bad_json_str, 1)
    assert result["success"] is False
    assert "error" in result
    assert "JSON parsing failed" in result["error"]

    # Test with missing key
    missing_key_json = '{"chapter": "content"}'
    result = chapter_generator._parse_chapter_response(missing_key_json, 1)
    assert result["success"] is False
    assert "error" in result
    assert "Response missing 'choices' field" in result["error"]

@patch('app.flows.generation.next_chapter_generator.BestsellerChapterGenerator._generate_single_version')
def test_generate_bestseller_chapter_game_mode(mock_generate_single, chapter_generator: BestsellerChapterGenerator):
    """Test that game mode correctly includes the user choice."""
    # Setup mock
    mock_version = MagicMock()
    mock_version.content = "Chapter content"
    mock_version.choices = []
    mock_generate_single.return_value = mock_version

    # Call the main method
    chapter_generator.generate_bestseller_chapter(
        story_title="Test Story",
        story_outline="Outline",
        story_dna_contexts=["DNA"],
        chapter_number=2,
        user_choice="User chose to fight.",
        is_game_mode=True,
        next_chapter_title="The Aftermath"
    )

    # Assert that the choice context was passed to the single version generator
    mock_generate_single.assert_called_once()
    call_args = mock_generate_single.call_args.kwargs
    assert "User chose to fight" in call_args["user_choice"]

@patch('app.flows.generation.next_chapter_generator.BestsellerChapterGenerator._generate_single_version')
def test_generate_bestseller_chapter_normal_mode(mock_generate_single, chapter_generator: BestsellerChapterGenerator):
    """Test that normal mode (non-game mode) does not pass the user choice."""
    # Setup mock
    mock_version = MagicMock()
    mock_version.content = "Chapter content"
    mock_version.choices = []
    mock_generate_single.return_value = mock_version

    # Call the main method
    chapter_generator.generate_bestseller_chapter(
        story_title="Test Story",
        story_outline="Outline",
        story_dna_contexts=["DNA"],
        chapter_number=2,
        user_choice="This should be ignored.",
        is_game_mode=False,
        next_chapter_title="The Aftermath"
    )

    # Assert that the choice context was empty
    mock_generate_single.assert_called_once()
    call_args = mock_generate_single.call_args.kwargs
    assert call_args["user_choice"] == ""
