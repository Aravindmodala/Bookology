from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def generate_summary(chapter_text):
    """
    Generates a 200-300 word summary for the given chapter text using OpenAI GPT-4o.
    The summary focuses on key events, character developments, and unresolved plot points.
    """
    prompt = (
        "Summarize the following story in 200-300 words, focusing on key events, character developments, and unresolved plot points and give the summary in 200 - 300 words, you are creating summary because we need to give the summary as input to LLM, so that it generates next subsequent chapater :\n\n"
        f"{chapter_text}\n\nSummary:"
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful book summarizer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()