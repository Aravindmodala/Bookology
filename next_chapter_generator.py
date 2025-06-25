"""
next_chapter_generator.py - Bookology Backend Utility

This file provides functions to generate the next chapter of a story using:
- The full outline for the story
- Relevant context from previous chapters (retrieved via vector search)
- OpenAI LLM for text generation

It is called from the FastAPI backend when a user wants to continue a saved story.
"""

from supabase import create_client
from dotenv import load_dotenv
import os

# Import your embedding/vector search and LLM utilities
# from chapter_embeddings import split_into_chunks  # if needed
# from your_llm_module import call_llm  # Replace with your actual LLM call

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def retrieve_relevant_chunks(story_id, previous_chapter_number, query_text, top_k=3):
    """
    Retrieves the most relevant chunks from the previous chapter using vector similarity.
    """
    # TODO: Query chapter_chunks where chapter_id = previous_chapter_id, order by similarity to query_text
    pass

# New: Always send the full outline to the LLM, and specify which chapter to generate

def build_next_chapter_prompt(full_outline, chapter_number, relevant_chunks):
    """
    Builds the prompt for the LLM to generate the next chapter.
    - full_outline: The entire story outline as a string.
    - chapter_number: The chapter to generate (e.g., 2).
    - relevant_chunks: List of strings from previous chapters.
    """
    prompt = f"""
Story Outline:
{full_outline}

Relevant content from previous chapters:
{chr(10).join(relevant_chunks)}

Instruction:
Write Chapter {chapter_number} of the story, following the outline above and using the relevant context. Continue the story naturally from the previous chapters.
"""
    return prompt


def generate_next_chapter(story_id, chapter_number, story_outline):
    """
    Main function to generate the next chapter.
    - Uses the full outline for context
    - Retrieves relevant context from previous chapter
    - Builds the prompt and calls the LLM
    - Returns the generated chapter text
    """
    # 1. Retrieve relevant chunks from previous chapter
    relevant_chunks = retrieve_relevant_chunks(story_id, chapter_number - 1, story_outline)
    # 2. Build prompt
    prompt = build_next_chapter_prompt(story_outline, chapter_number, relevant_chunks)
    # 3. Call LLM (pseudo-code)
    # next_chapter = call_llm(prompt)
    # return next_chapter
    pass
