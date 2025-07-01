"""
story_chatbot.py - Bookology GenAI Multiverse Chatbot (LangChain Edition)

Features:
- Per-user, per-story conversational memory (LangChain ConversationBufferMemory)
- Retrieval-augmented generation (RAG) with pgvector/Supabase
- Intent classification (query, modify, multiverse, etc.)
- Modular, extensible, and production-ready
- Debugging and observability for prompt engineering
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_postgres import PGVector
from supabase import create_client
from uuid import uuid4
import psycopg  # Add this import
import urllib.parse
import socket

load_dotenv()

# --- Config ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_CONNECTION_STRING")  # e.g. postgresql+psycopg2://user:pass@host:port/db

print("SUPABASE_CONNECTION_STRING:", repr(SUPABASE_CONNECTION_STRING))

# Force IPv4 preference - commented out to avoid recursion
# socket.getaddrinfo = lambda host, port, family=socket.AF_UNSPEC, *args, **kwargs: socket.getaddrinfo(host, port, socket.AF_INET, *args, **kwargs) if family == socket.AF_UNSPEC else socket.getaddrinfo(host, port, family, *args, **kwargs)

# --- LLM and Embeddings ---
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o")
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# --- Supabase Client (for user/story validation, etc.) ---
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Vector Store Setup ---
# Use only the working connection string (original format)
print(f"DEBUG: Using connection string: {SUPABASE_CONNECTION_STRING}")
try:
    vectorstore = PGVector(
        embeddings=embeddings,
        connection=SUPABASE_CONNECTION_STRING,
        collection_name="chapter_chunks",
        use_jsonb=True
    )
    print("DEBUG: Vector store initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize vector store: {e}")
    raise e

# --- Memory Management ---
# We'll keep a memory object per (user_id, story_id) session
class MemoryManager:
    def __init__(self):
        self._memories = {}

    def get_memory(self, user_id: str, story_id: str) -> ConversationBufferMemory:
        key = f"{user_id}:{story_id}"
        if key not in self._memories:
            self._memories[key] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        return self._memories[key]

memory_manager = MemoryManager()

# --- Intent Classification ---
def classify_intent(llm, message: str) -> str:
    prompt = f"""
Classify the user's intent from their message. Choose one:
- 'query': Asking about story content
- 'modify': Wanting to change or rewrite story elements
- 'multiverse': Wanting to connect this story with other stories
- 'other': Anything else

User message: \"{message}\"

Intent (one word):
"""
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    print(f"[DEBUG] Intent classified as: {intent}")
    return intent

# --- Conversational Retrieval Chain Factory ---
def get_qa_chain(user_id: str, story_id: str):
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5, "filter": {"story_id": story_id}}
    )
    memory = memory_manager.get_memory(user_id, story_id)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True
    )
    return chain

# --- Main Chatbot Class ---
class StoryChatbot:
    def __init__(self):
        self.llm = llm
        self.supabase = supabase

    def chat(
        self,
        user_id: str,
        story_id: str,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main chat entrypoint. Handles intent, memory, and RAG.
        """
        try:
            print(f"[DEBUG] Chat request - User: {user_id}, Story: {story_id}, Message: {message}")

            # 1. Validate user/story
            print(f"[DEBUG] Validating user owns story...")
            if not self._user_owns_story(user_id, story_id):
                return {"type": "error", "content": "You do not own this story."}

            # 2. Classify intent
            print(f"[DEBUG] Classifying intent...")
            intent = classify_intent(self.llm, message)
            print(f"[DEBUG] Intent classified as: {intent}")

            # 3. Route by intent
            if intent == "query":
                return self._handle_query(user_id, story_id, message)
            elif intent == "modify":
                return self._handle_modify(user_id, story_id, message)
            elif intent == "multiverse":
                return self._handle_multiverse(user_id, story_id, message)
            else:
                return {
                    "type": "unknown",
                    "content": "I'm not sure what you'd like to do. You can ask questions about your story, request modifications, or create connections with your other stories.",
                    "intent": intent
                }
        except Exception as e:
            print(f"[ERROR] Chat function failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "type": "error",
                "content": f"Sorry, I encountered an error: {str(e)}"
            }

    def _handle_query(self, user_id, story_id, message):
        print(f"[DEBUG] Handling story query for story {story_id}")
        try:
            print(f"[DEBUG] Creating QA chain...")
            qa_chain = get_qa_chain(user_id, story_id)
            print(f"[DEBUG] QA chain created, running query...")
            result = qa_chain({"question": message})
            print(f"[DEBUG] QA Chain Result: {result['answer'][:100]}...")
            return {
                "type": "answer",
                "content": result["answer"],
                "sources": [doc.metadata for doc in result.get("source_documents", [])]
            }
        except Exception as e:
            print(f"[ERROR] Query handling failed: {e}")
            return {
                "type": "error",
                "content": f"Sorry, I encountered an error while searching your story: {str(e)}"
            }

    def _handle_modify(self, user_id, story_id, message):
        print(f"[DEBUG] Handling story modification for story {story_id}")
        # Advanced: Use LLM to analyze and rewrite story content, then update DB and embeddings
        # For now, just acknowledge
        return {
            "type": "modification_request",
            "status": "pending",
            "message": "Story modification requests are coming soon! (This will let you rewrite chapters, change plots, etc.)"
        }

    def _handle_multiverse(self, user_id, story_id, message):
        print(f"[DEBUG] Handling multiverse request for user {user_id}, story {story_id}")
        # Advanced: Search across all user's stories, allow character/plot crossovers, etc.
        # For now, just acknowledge
        user_stories = self.supabase.table("Stories").select("id,story_title").eq("user_id", user_id).execute()
        return {
            "type": "multiverse_request",
            "status": "pending",
            "message": f"You have {len(user_stories.data)} stories. Multiverse features are coming soon!",
            "available_stories": [story["story_title"] for story in user_stories.data]
        }

    def _user_owns_story(self, user_id, story_id):
        # Check if the user owns the story
        result = self.supabase.table("Stories").select("id").eq("id", story_id).eq("user_id", user_id).single().execute()
        return bool(result.data)

# --- Global instance ---
story_chatbot = StoryChatbot()
