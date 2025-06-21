# main.py
from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from book_generator import generate_book_from_outline
from movie_script_generator import generate_movie_script
from book_generator_prompt import book_prompt
from fastapi.middleware.cors import CORSMiddleware
from lc_book_generator_prompt import generate_book_outline
from lc_book_generator import generate_chapter_from_outline

app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount templates directory
templates = Jinja2Templates(directory="templates")

class StoryInput(BaseModel):
    idea: str
    format: str  # "book" or "movie"
    generate_chapter: bool = False

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
def generate_story(data: StoryInput):
    if data.format == "book":
        # Always generate outline only
        result = book_prompt(data.idea)
    elif data.format == "movie":
        result = generate_movie_script(data.idea)
    else:
        return {"error": "Invalid format"}
    
    return {"expanded_prompt": result}


@app.post("/generate_chapter")
def generate_chapter(payload: dict = Body(...)):
    outline = payload.get("outline")
    if not outline:
        return {"error": "Missing outline"}
    chapter = generate_book_from_outline(outline)
    return {"chapter_1": chapter}

@app.post("/lc_generate_outline")
def lc_generate_outline(data: dict = Body(...)):
    idea = data.get("idea")
    if not idea:
        return {"error": "Missing idea"}
    result = generate_book_outline(idea)
    return {"expanded_prompt": result}

@app.post("/lc_generate_chapter")
def lc_generate_chapter(data: dict = Body(...)):
    outline = data.get("outline")
    if not outline:
        return {"error": "Missing outline"}
    result = generate_chapter_from_outline(outline)
    return {"chapter_1": result}
