from supabase import create_client
from dotenv import load_dotenv
import os
from Generate_summary import generate_summary  # <-- Import the summary function
from openai import OpenAI
from chapter_embeddings import embed_and_store_chunks  # Import embedding function

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
            {"role": "system", "content": "You are a helpful and creative book-writing assistant who wrote a lot of best selling books that turned out to be big hit movies too ."},
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
    Also generates embeddings for vector search.
    """
    print(f"[DEBUG] Generating summary for chapter {chapter_number}...")
    summary = generate_summary(chapter_text)
    print(f"[DEBUG] Summary generated. Saving chapter {chapter_number} to database...")
    
    # Insert chapter with summary
    result = supabase.table("Chapters").insert({
        "story_id": story_id,
        "chapter_number": chapter_number,
        "content": chapter_text,
        "summary": summary
    }).execute()
    
    if not result.data or "id" not in result.data[0]:
        raise Exception(f"Failed to save chapter {chapter_number}")
    
    chapter_id = result.data[0]["id"]
    print(f"[DEBUG] Chapter {chapter_number} and summary saved.")
    
    # Generate embeddings for vector search
    print(f"[DEBUG] Generating embeddings for chapter {chapter_number}...")
    embed_and_store_chunks(chapter_id, chapter_text)
    print(f"[DEBUG] Embeddings generated and stored for chapter {chapter_number}.")
    
    return chapter_id

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
    print(f"[DEBUG] Story Outline for story_id={story_id}:\n{outline}\n---END OUTLINE---\n")
    summaries = get_previous_summaries(story_id, chapter_number)
    print(f"[DEBUG] Previous Summaries for story_id={story_id}, upto_chapter_number={chapter_number}:")
    for idx, summary in enumerate(summaries, 1):
        print(f"  [Summary {idx}]:\n{summary}\n---END SUMMARY---\n")
    
    # Build a more detailed prompt for better continuity
    prompt = f"""
🎬 You are a master storyteller creating Chapter {chapter_number} of a bestselling novel.

📚 STORY OUTLINE:
{outline}

📖 PREVIOUS CHAPTER SUMMARIES (for continuity):
{chr(10).join(summaries)}

🎯 YOUR TASK:
Write Chapter {chapter_number} that seamlessly continues the story. You MUST:

1. **Follow the outline structure** - Check what Chapter {chapter_number} should cover according to the outline
2. **Maintain character consistency** - Use the same character names, personalities, and relationships from previous chapters
3. **Continue plot threads** - Pick up unresolved plot points from previous summaries
4. **Maintain tone and style** - Keep the same writing style and emotional tone
5. **Create smooth transitions** - Start where the previous chapter left off
6. **End with a compelling cliffhanger** - Make readers desperate for the next chapter

📝 WRITING REQUIREMENTS:
- Write in novel format (not script format)
- Use the same perspective as previous chapters
- Include character dialogue and internal thoughts
- Build emotional tension and drama
- Make it feel like a natural continuation, not a disconnected chapter

⚠️ CRITICAL: This chapter must feel like a direct continuation of the previous chapters. Reference events, characters, and situations from the summaries above to maintain perfect continuity.

Start writing Chapter {chapter_number} now:
"""
    print(f"[DEBUG] Final Prompt for LLM (story_id={story_id}, chapter_number={chapter_number}):\n{prompt}\n---END PROMPT---\n")
    print("[DEBUG] Prompt built with outline and summaries.")
    return prompt

def generate_next_chapter(story_id, chapter_number):
    print(f"[DEBUG] Generating next chapter {chapter_number} for story_id={story_id}")
    prompt = build_next_chapter_prompt_with_summaries(story_id, chapter_number)
    next_chapter = call_llm(prompt)
    print(f"[DEBUG] Next chapter {chapter_number} generated.")
    return next_chapter