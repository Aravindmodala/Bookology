"""
main.py - Bookology Backend API

This file is the main entry point for the Bookology backend, built with FastAPI. It exposes API endpoints for generating, saving, and retrieving stories and chapters, and handles authentication, chunking, and embedding logic for vector search. It connects to a Supabase Postgres database and uses OpenAI for LLM and embeddings.

Data Flow:
- The frontend (React) calls these endpoints to generate outlines/chapters and to save stories.
- When a story is saved, chapter 1 is also saved and chunked/embedded for vector search.
- All chapter content and embeddings are stored in Supabase tables (Stories, Chapters, chapter_chunks).
- The backend is responsible for orchestrating all business logic and data movement between frontend and database.

"""
# main.py
# Bookology Backend API
# This file implements the FastAPI backend for Bookology, handling story and chapter generation, saving, authentication, and vector embedding for smart retrieval.
# The backend connects to Supabase for data storage and uses OpenAI for LLM and embedding services.

from fastapi import FastAPI, Request, Body, Depends, HTTPException, BackgroundTasks  # FastAPI core imports
from fastapi.responses import HTMLResponse  # For serving HTML pages
from fastapi.staticfiles import StaticFiles  # For serving static files (not used here)
from fastapi.templating import Jinja2Templates  # For rendering HTML templates
from pydantic import BaseModel  # For request/response data validation
from movie_script_generator import generate_movie_script  # Movie script generation logic
from fastapi.middleware.cors import CORSMiddleware  # For handling CORS (frontend-backend communication)
from lc_book_generator_prompt import generate_book_outline  # Book outline generation (LangChain)
from lc_book_generator import generate_chapter_from_outline  # Chapter generation from outline (LangChain)
import os  # For environment variable access
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # For token-based authentication
from dotenv import load_dotenv  # For loading .env config
from supabase import create_client, Client  # Supabase client for database access
from chapter_embeddings import embed_and_store_chunks  # Function to chunk, embed, and store chapter content

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins (for development; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Jinja2 templates directory for HTML rendering
templates = Jinja2Templates(directory="templates")

# --- Supabase Client Initialization ---
# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# Create Supabase client for database operations
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Pydantic Models for Request Validation ---
class StoryInput(BaseModel):
    idea: str  # The user's story idea
    format: str  # "book" or "movie"
    generate_chapter: bool = False  # Whether to generate a chapter immediately

class StorySaveInput(BaseModel):
    story_outline: str  # The generated outline for the story
    chapter_1_content: str  # The generated content for chapter 1
    story_title: str  # The title of the story

class ChapterInput(BaseModel):
    story_id: int  # Foreign key to the story
    chapter_number: int  # Chapter number in the story
    content: str  # The actual chapter text

# --- Authentication Scheme ---
auth_scheme = HTTPBearer()  # HTTP Bearer token authentication for protected endpoints

# --- API Endpoints ---

print("main.py loaded and running")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    Serves the main HTML page for the Bookology app.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
def generate_story(data: StoryInput):
    """
    Generates a story outline (for books) or a movie script (for movies) based on the user's idea.
    """
    if data.format == "book":
        # Generate a book outline using the prompt logic
        result = book_prompt(data.idea)
    elif data.format == "movie":
        # Generate a movie script
        result = generate_movie_script(data.idea)
    else:
        return {"error": "Invalid format"}
    return {"expanded_prompt": result}

@app.post("/generate_chapter")
def generate_chapter(payload: dict = Body(...)):
    """
    Generates a book chapter from a given outline.
    """
    outline = payload.get("outline")
    if not outline:
        return {"error": "Missing outline"}
    chapter = generate_book_from_outline(outline)
    return {"chapter_1": chapter}

@app.post("/lc_generate_outline")
def lc_generate_outline(data: dict = Body(...)):
    """
    Generates a book outline using LangChain's LLM chain.
    """
    idea = data.get("idea")
    if not idea:
        return {"error": "Missing idea"}
    result = generate_book_outline(idea)
    return {"expanded_prompt": result}

@app.post("/lc_generate_chapter")
def lc_generate_chapter(data: dict = Body(...)):
    """
    Generates a chapter using LangChain's LLM chain from a given outline.
    """
    outline = data.get("outline")
    if not outline:
        return {"error": "Missing outline"}
    result = generate_chapter_from_outline(outline)
    return {"chapter_1": result}

@app.post("/stories/save")
def save_story(story_data: StorySaveInput, token: HTTPAuthorizationCredentials = Depends(auth_scheme), background_tasks: BackgroundTasks = None):
    """
    Saves a new story to the Stories table and also saves Chapter 1 to the Chapters table.
    After saving Chapter 1, it splits the chapter into chunks, generates embeddings for each chunk,
    and stores them in the chapter_chunks table for vector search and smart retrieval.
    The chunking/embedding is run as a background task.
    """
    print("==== /stories/save endpoint called ====")  # Debug print
    try:
        # Verify the user's token to get their user data
        user_response = supabase.auth.get_user(token.credentials)
        user = user_response.user
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Prepare the data for insertion into Stories
        data_to_insert = {
            "user_id": user.id,
            "story_outline": story_data.story_outline,
            "story_title": story_data.story_title,
        }

        # Insert the story into the 'Stories' table
        response = supabase.table('Stories').insert(data_to_insert).execute()
        story_id = response.data[0]["id"]

        # Insert chapter 1 into Chapters table
        chapter_data = {
            "story_id": story_id,
            "chapter_number": 1,
            "content": story_data.chapter_1_content
        }
        chapter_result = supabase.table("Chapters").insert(chapter_data).execute()
        if not chapter_result.data or "id" not in chapter_result.data[0]:
            raise HTTPException(status_code=500, detail="Failed to save chapter 1")
        chapter_id = chapter_result.data[0]["id"]

        print(f"[Main thread] Scheduling embedding function for chapter_id: {chapter_id}")  # Debug print
        if background_tasks is not None:
            background_tasks.add_task(embed_and_store_chunks, chapter_id, story_data.chapter_1_content)
            print("[Main thread] Embedding task added to background tasks queue.")
        else:
            print("[Main thread] BackgroundTasks not available, running synchronously.")
            embed_and_store_chunks(chapter_id, story_data.chapter_1_content)

        return {"message": "Story and Chapter 1 saved successfully! Embedding will be processed in the background.", "story_id": story_id, "chapter_id": chapter_id}

    except Exception as e:
        print("Save story error:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_chapter/")
def save_chapter(chapter: ChapterInput):
    """
    Saves a chapter to the Chapters table and then splits the chapter into chunks,
    generates embeddings for each chunk, and stores them in the chapter_chunks table.
    This enables vector search and smart retrieval for long chapters.
    """
    # Insert chapter (without embedding)
    data = {
        "story_id": chapter.story_id,
        "chapter_number": chapter.chapter_number,
        "content": chapter.content
    }
    result = supabase.table("Chapters").insert(data).execute()
    if not result.data or "id" not in result.data[0]:
        raise HTTPException(status_code=500, detail="Failed to save chapter")
    chapter_id = result.data[0]["id"]

    # Chunk, embed, and store chapter content for vector search
    embed_and_store_chunks(chapter_id, chapter.content)
    return {"message": "Chapter saved and embedding stored!", "chapter_id": chapter_id}
