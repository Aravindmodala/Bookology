from langchain_community.llms import OpenAI  # Or switch to `langchain_openai` if needed
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Initialize the LLM (OpenAI model)
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7, max_tokens=2000)

# Create a prompt template for generating Chapter 1 from an outline
prompt = PromptTemplate(
    input_variables=["outline"],
    template="""
You are a globally renowned novelist, ghostwriter, and master storyteller.

Your task is to take the following fully expanded story outline and write **one emotionally immersive, professionally written Chapter 1** of a novel that feels like it belongs on a bestselling shelf.

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
)

# Build the chain
chapter_chain = LLMChain(llm=llm, prompt=prompt)

def generate_chapter_from_outline(outline: str):
    try:
        result = chapter_chain.invoke({"outline": outline})
        return result["text"].strip()  # <-- This returns to FastAPI
    except Exception as e:
        return f"❌ Error generating Chapter 1: {str(e)}"

