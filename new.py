import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from prompt_expander import expand_prompt

# Load your OpenAI API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Step 1: User's raw idea
user_input = "give me a love story where the main character dies in the end but the love story is so strong that it makes the reader cry"

# Step 2: Expand that into a rich cinematic prompt using GPT-4o
rich_prompt = expand_prompt(user_input)

# Step 3: Story generation
start_time = time.time()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are a masterful fiction author who writes cinematic, emotionally immersive stories with regional Indian flavor, gripping twists, and cliffhangers."
        },
        {
            "role": "user",
            "content": rich_prompt
        }
    ],
    max_tokens=5000,
    temperature=0.85,
    top_p=0.95
)

end_time = time.time()

# Output results
print(f"\n⏱️ Generation Time: {end_time - start_time:.2f} seconds")
print("\n🧠 Expanded Prompt:\n", rich_prompt)
print("\n🎬 Generated Story:\n", response.choices[0].message.content)
