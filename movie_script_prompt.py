import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def expand_prompt(user_input: str) -> str:
    system_message = """
You are a masterful screenwriter and story architect.
Your task is to take a simple movie idea and expand it into a detailed cinematic blueprint.
Focus on:
- Visual storytelling elements
- Character arcs and motivations
- Scene-by-scene breakdown
- Emotional beats
- Plot structure
- Cinematic moments
- Theme and tone
"""
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ],
        temperature=0.8,
        max_tokens=2000
    )
    
    return response.choices[0].message.content


if __name__ == "__main__":
    prompt = expand_prompt(
        "generate a periodical gangster drama in telugu with guns and girls, focusing on the rise and fall of a notorious crime family. The story should explore themes of loyalty, betrayal, and the cost of ambition"
    )
    print("\n\nExpanded Prompt:\n", prompt)
