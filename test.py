from dotenv import load_dotenv
import os

load_dotenv()
print("hello")
print(os.getenv("OpenAI_API_KEY"))