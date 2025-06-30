from supabase import create_client
from dotenv import load_dotenv
import os
from Generate_summary import generate_summary  # <-- Import the summary function
from openai import OpenAI

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key)

def call_llm(prompt):
    """
    Calls the OpenAI LLM to generate the next chapter.
    """
    print("[DEBUG] Calling LLM to generate next chapter...")
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful and creative book-writing assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0.8
    )
    print("[DEBUG] LLM response received.")
    return response.choices[0].message.content.strip()

def save_chapter(story_id, chapter_number, chapter_text):
    """
    Saves the chapter and its summary to the database.
    """
    print(f"[DEBUG] Generating summary for chapter {chapter_number}...")
    summary = generate_summary(chapter_text)
    print(f"[DEBUG] Summary generated. Saving chapter {chapter_number} to database...")
    supabase.table("Chapters").insert({
        "story_id": story_id,
        "chapter_number": chapter_number,
        "content": chapter_text,
        "summary": summary
    }).execute()
    print(f"[DEBUG] Chapter {chapter_number} and summary saved.")

def get_previous_summaries(story_id, upto_chapter_number):
    resp = supabase.table("Chapters") \
        .select("chapter_number,summary") \
        .eq("story_id", story_id) \
        .lt("chapter_number", upto_chapter_number) \
        .order("chapter_number") \
        .execute()
    return [row["summary"] for row in resp.data if row["summary"]]

def get_story_outline(story_id):
    resp = supabase.table("Stories").select("story_outline").eq("id", story_id).single().execute()
    return resp.data["story_outline"] if resp.data else ""

def build_next_chapter_prompt_with_summaries(story_id, chapter_number):
    outline = get_story_outline(story_id)
    summaries = get_previous_summaries(story_id, chapter_number)
    prompt = f"""
Story Outline:
{outline}

Summaries of Previous Chapters:
{chr(10).join(summaries)}

Instruction:
Write Chapter {chapter_number} of the story, following the outline and using the summaries above for context. Continue the story naturally and end with a cliffhanger.
"""
    print("[DEBUG] Prompt built with outline and summaries.")
    return prompt

def generate_next_chapter(story_id, chapter_number):
    print(f"[DEBUG] Generating next chapter {chapter_number} for story_id={story_id}")
    prompt = build_next_chapter_prompt_with_summaries(story_id, chapter_number)
    next_chapter = call_llm(prompt)
    print(f"[DEBUG] Next chapter {chapter_number} generated.")
    return next_chapter