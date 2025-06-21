import os
from openai import OpenAI
from dotenv import load_dotenv
from book_generator_prompt import book_prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_book_from_outline(outline: str) -> str:
    system_message = """
You are a globally renowned novelist, ghostwriter, and master storyteller.

Your task is to take a fully expanded story outline and write **one emotionally immersive, professionally written chapter** of a novel that feels like it belongs on a bestselling shelf.

--- 

📘 STORY OUTLINE:
{outline}

---

🎯 OBJECTIVE:
Write **Chapter 1** of this novel. Follow the chapter description and structure given in the outline. The chapter must:

1. Begin with an emotionally gripping or atmospheric hook  
2. Introduce or re-establish the main characters with rich depth — not just facts, but emotions, inner flaws, secrets, or memories  
3. Build tension, emotion, or mystery through:
   - Dialogue
   - Internal monologue
   - Descriptive world-building (sights, sounds, sensations)
   - Character conflict or decisions  
4. Progress the story in a meaningful way (emotionally or plot-wise)  
5. End on a compelling cliffhanger that makes the reader **desperate for the next chapter** — like a reveal, betrayal, twist, or shocking action

---

✍️ WRITING STYLE:
- Format: **Novel-style prose**, not a script or bullet points
- Voice: Write as if this was penned by a masterful human author
- Perspective: Use third-person limited (or first-person if the outline suggests it)
- Language: Vivid, dramatic, and emotionally expressive — avoid robotic tone
- Make characters feel alive — full of contradictions, depth, and vulnerability
- Build the **first few paragraphs of Chapter 1** to make readers feel *this is a real book*, not AI output

---

📌 START FORMAT:
**Chapter 1: [Use the Chapter Title from the outline]**

(Then begin the chapter)

---

DO NOT:
- Explain the outline
- Return summaries
- Repeat any outline section
- Say "As per the outline..."

Just write the actual chapter content. Make it so immersive that the reader forgets it was written by a machine.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Using this outline, write Chapter 1:\n\n{outline}"}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    return response.choices[0].message.content

