from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Initialize the LLM (OpenAI model)
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.8, max_tokens=2000)

# Create a prompt template
prompt = PromptTemplate(
    input_variables=["idea"],
    template="""🎬 You are a world-class Telugu action screenwriter known for crafting mass-entertainment blockbusters with emotional depth and explosive sequences.

Take the following idea and expand it into a **full-length novel blueprint** in the style of a Telugu action thriller film. Stay true to the genre, tone, and cinematic universe it belongs to.

🧠 INPUT IDEA:
"{idea}"

---

Your output should be grounded in:
- 
- **Cultural context** (Telugu culture, language, cinema tone)
- **Casting** (Include actors from the input in character roles)
- **Genre accuracy** (Massy action, revenge drama, emotion, powerful dialogue)
- **Setting** (South Indian towns, cities, rural-urban contrast)

📚 OUTPUT FORMAT:
1. A good title that captures the essence of the story
2.Total number of chapters (15–20 chapters)
3: Genre & Emotional Intent  
4: Setting & World-Building  
5: Character Design (Hero, Villain, Heroine, Supporting Cast)  
6: Chapter-by-Chapter Breakdown (15–20 chapters)  
7: Style & Language (Tone, perspective, voice)  
8: Symbols, Motifs, Recurring Visuals

🧨 Final Note: Write like you're pitching a high-budget Telugu movie with a gripping story, unforgettable characters, and whistle-worthy scenes.
"""
)

# Build the chain
chain = prompt | llm

# Format and display the output nicely
def generate_book_outline(idea: str):
    try:
        result = chain.invoke({"idea": idea})
        return result.strip()
    except Exception as e:
        return f"❌ Error generating book outline: {str(e)}"

# Entry point