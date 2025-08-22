import pytest
import json
from unittest.mock import patch, MagicMock

# Adjust path to import the app module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.dna_extractor import EnhancedLLMStoryDNAExtractor

@pytest.fixture
def extractor():
    """Provides a fresh EnhancedLLMStoryDNAExtractor instance for each test."""
    return EnhancedLLMStoryDNAExtractor()

# To mock the .content attribute of a LangChain AIMessage
class MockAIMessage:
    def __init__(self, content):
        self.content = content

# Sample data for testing
SAMPLE_CHAPTER_CONTENT = "John walked into the room. 'I have the amulet,' he said. Mary gasped. The amulet was the key to everything. They had to decide what to do next. The fate of the kingdom was in their hands."
SAMPLE_PREVIOUS_DNA = [{
    "chapter_number": 1,
    "plot_genetics": {
        "active_plot_threads": [{"thread_id": "t1", "description": "Find the amulet", "status": "ongoing"}]
    }
}]
SAMPLE_LLM_DNA_RESPONSE = {
    "scene_genetics": {"location_description": "A dusty room"},
    "character_genetics": {"active_characters": ["John", "Mary"]},
    "plot_genetics": {
        "active_plot_threads": [
            {"thread_id": "t1", "description": "Find the amulet", "status": "resolved"},
            {"thread_id": "t2", "description": "Decide what to do with the amulet", "status": "introduced"}
        ]
    },
    "choice_genetics": {}, "emotional_genetics": {}, "ending_genetics": {},
    "continuity_anchors": [], "world_building": {}
}

def test_build_previous_context(extractor: EnhancedLLMStoryDNAExtractor):
    """Test the _build_previous_context helper method."""
    # Test with no previous DNA
    context = extractor._build_previous_context([])
    assert "no previous context" in context

    # Test with previous DNA
    context = extractor._build_previous_context(SAMPLE_PREVIOUS_DNA)
    assert "CHAPTER 1 SUMMARY" in context
    assert "Find the amulet" in context

def test_track_plot_evolution(extractor: EnhancedLLMStoryDNAExtractor):
    """Test the _track_plot_evolution helper method."""
    current_dna = SAMPLE_LLM_DNA_RESPONSE

    result_dna = extractor._track_plot_evolution(current_dna, SAMPLE_PREVIOUS_DNA)

    assert "plot_evolution" in result_dna
    evolution = result_dna["plot_evolution"]
    assert "Find the amulet" not in evolution["threads_dropped"] # It was resolved, not dropped
    assert "Decide what to do with the amulet" in evolution["threads_new"]

@patch('app.services.dna_extractor.EnhancedLLMStoryDNAExtractor._extract_enhanced_dna_with_llm')
def test_extract_chapter_dna_success(mock_extract_llm, extractor: EnhancedLLMStoryDNAExtractor):
    """Test the main extract_chapter_dna method for a successful extraction."""
    # Configure the mock for the LLM extraction part
    mock_extract_llm.return_value = SAMPLE_LLM_DNA_RESPONSE

    result = extractor.extract_chapter_dna(
        chapter_content=SAMPLE_CHAPTER_CONTENT,
        chapter_number=2,
        previous_dna_list=SAMPLE_PREVIOUS_DNA
    )

    mock_extract_llm.assert_called_once()
    assert result["chapter_number"] == 2
    assert result["extraction_method"] == "ENHANCED_LLM"
    assert "plot_evolution" in result # Check that post-processing was called

@patch('app.services.dna_extractor.EnhancedLLMStoryDNAExtractor._extract_enhanced_dna_with_llm')
def test_extract_chapter_dna_llm_failure(mock_extract_llm, extractor: EnhancedLLMStoryDNAExtractor):
    """Test the main extract_chapter_dna method when the LLM extraction fails."""
    # Configure the mock to raise an exception
    mock_extract_llm.side_effect = Exception("LLM call failed")

    result = extractor.extract_chapter_dna(
        chapter_content=SAMPLE_CHAPTER_CONTENT,
        chapter_number=2
    )

    assert result["extraction_status"] == "fallback"
    assert "Complete extraction failure" in result["fallback_reason"]
    assert "final_scene_context" in result["ending_genetics"]
