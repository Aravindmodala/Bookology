import os
from openai import OpenAI
from dotenv import load_dotenv
from movie_script_prompt import expand_prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_movie_script(user_input: str) -> str:
    # First, get the expanded prompt
    expanded_prompt = expand_prompt(user_input)
    
    # Now generate the actual movie script using the expanded prompt
    system_message = """
🎥 You are a legendary screenwriter and cinematic storyteller known for writing blockbuster films across languages and genres.

Your job is to take a rich, detailed story outline and generate a **professional movie script**, written scene-by-scene with cinematic pacing, visual direction, and emotionally charged dialogue.
---
📘 STORY OUTLINE:
{Insert the expanded outline here — including genre, characters, setting, emotional tone, scene/chapter breakdowns, and theme}
---

🎯 OBJECTIVE:
Write **Scene {scene_number}** of this movie script based on the outline.
This scene must:
1. Begin with a visual setup of the location and mood (use INT. / EXT. properly)
2. Introduce or follow up with key characters **through action**, **not exposition**
3. Build emotional tension using:
   - Sharp, natural-sounding dialogue
   - Action and reaction
   - Subtext, silence, or interruptions
4. Show the characters' **emotional states, intentions, and stakes**
5. End with a **cinematic beat** or **scene-level cliffhanger** that drives the story forward
---
🖋️ SCREENWRITING STYLE:
- Format: **Proper screenplay format**
- Use scene headers like: `INT. MEERA'S LAW OFFICE – NIGHT`
- Keep action lines short, visual, and dynamic
- Dialogue should reflect each character's personality and inner world
- Use pauses, interruptions, and inner tension naturally
- Include cinematic cues (e.g., "The camera slowly zooms in…" or "We hear the sound of distant thunder…") *sparingly*, only when it enhances immersion
---
🎞️ START FORMAT:
"""
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Using this outline, write a complete movie script:\n\n{expanded_prompt}"}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    # Test the generator
    user_idea = input("Enter your movie idea: ")
    print("\nGenerating your movie script...\n")
    script = generate_movie_script(user_idea)
    print("\n=== Your Generated Movie Script ===\n")
    print(script) 