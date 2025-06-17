# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from prompt_expander import expand_prompt
from book_generator_prompt import book_prompt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoryInput(BaseModel):
    idea: str
    format: str  # "book" or "script"

@app.post("/generate")
def generate_story(data: StoryInput):
    if data.format == "book":
        prompt = book_prompt(data.idea)
    elif data.format == "script":
        prompt = expand_prompt(data.idea)
    else:
        return {"error": "Invalid format"}
    
    return {"expanded_prompt": prompt}
