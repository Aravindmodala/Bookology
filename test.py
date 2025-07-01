from dotenv import load_dotenv
import os
from openai import OpenAI
import psycopg2

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
conn_str = os.getenv("SUPABASE_PG_DSN")
print("Connection string:", repr(conn_str))

try:
    conn = psycopg2.connect(conn_str)
    print("Connection successful!")
except Exception as e:
    print("Connection failed:", e)

def generate_summary(chapter_text):
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

if __name__ == "__main__":
    print("hello")
    print("Please paste your story below. Press Enter, then Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) to finish input:")
    story = ""
    try:
        while True:
            line = input()
            story += line + "\n"
    except EOFError:
        pass

    summary = generate_summary(story)
    print("\n--- Story Summary ---\n")
    print(summary)