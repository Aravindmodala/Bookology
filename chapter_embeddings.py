"""
chapter_embeddings.py - Bookology Backend Utility

This file provides utility functions for chunking chapter text and generating/storing embeddings using OpenAI. It is called from main.py after a chapter is saved, either directly or as a FastAPI background task. All chunked data and embeddings are stored in the chapter_chunks table in Supabase for vector search and retrieval.
"""
from langchain_community.embeddings import OpenAIEmbeddings
from supabase import create_client
from dotenv import load_dotenv
import os
import uuid

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
openai_embedder = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-ada-002")

# Step 1: Split text into ~200-word chunks
def split_into_chunks(text, max_words=200):
    """
    Splits the input text into chunks of approximately max_words words each.
    """
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

# Step 2: Embed and insert each chunk into chapter_chunks
def embed_and_store_chunks(chapter_id, chapter_text):
    """
    Splits the chapter text into chunks, generates embeddings for each chunk,
    and inserts them into the chapter_chunks table in Supabase.
    Includes debug print statements for tracing execution.
    """
    try:
        print(f"=== embed_and_store_chunks CALLED for chapter_id: {chapter_id} ===")
        chunks = split_into_chunks(chapter_text)
        print(f"Total chunks to process: {len(chunks)}")

        # Batch embed all chunks for efficiency
        vectors = openai_embedder.embed_documents(chunks)
        print("Embedding complete. Inserting into Supabase...")

        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            try:
                # Insert each chunk and its embedding into the chapter_chunks table
                response = supabase.table("chapter_chunks").insert({
                    "id": str(uuid.uuid4()),  # Ensure your DB column is uuid or text
                    "chapter_id": chapter_id,
                    "chunk_index": i,
                    "content_chunk": chunk,
                    "embedding": vector
                }).execute()
                print(f"Inserted chunk {i} successfully ✅ (chunk length: {len(chunk)} chars)")
            except Exception as e:
                print(f"❌ Error embedding or inserting chunk {i}: {e}")
        print(f"=== Finished processing chapter_id: {chapter_id} ===")
    except Exception as e:
        print(f"Error in embed_and_store_chunks (chapter_id: {chapter_id}): {e}")
