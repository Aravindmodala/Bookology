# Verbatim migration of story_chatbot.py into app/services/chatbot.py
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import traceback

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_postgres import PGVector
from supabase import create_client, Client

from app.core.config import settings
from app.core.logger_config import logger
from exceptions import (
    ChatbotError, AuthorizationError, StoryNotFoundError,
    VectorStoreError, DatabaseConnectionError
)


class IntentType(Enum):
    QUERY = "query"
    MODIFY = "modify"
    MULTIVERSE = "multiverse"
    OTHER = "other"


@dataclass
class ChatResponse:
    type: str
    content: str
    intent: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryManager:
    def __init__(self):
        self._memories: Dict[str, ConversationBufferMemory] = {}
        logger.info("Memory manager initialized")
    
    def get_memory(self, user_id: str, story_id: str) -> ConversationBufferMemory:
        session_key = f"{user_id}:{story_id}"
        if session_key not in self._memories:
            self._memories[session_key] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer",
            )
            logger.info(f"Created new memory session for {session_key}")
        return self._memories[session_key]
    
    def clear_memory(self, user_id: str, story_id: str) -> None:
        session_key = f"{user_id}:{story_id}"
        if session_key in self._memories:
            del self._memories[session_key]
            logger.info(f"Cleared memory session for {session_key}")


class IntentClassifier:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._classification_prompt = self._build_classification_prompt()
    
    def _build_classification_prompt(self) -> str:
        return """
You are an AI assistant that classifies user intents for a story interaction system.

Analyze the user's message and classify their intent into one of these categories:

1. 'query': User is asking questions about story content, characters, plot, or seeking information
   Examples: "What happened in chapter 3?", "Who is the main character?", "Summarize the story"

2. 'modify': User wants to change, rewrite, or modify story elements
   Examples: "Rewrite chapter 2", "Change the ending", "Make the character stronger"

3. 'multiverse': User wants to connect this story with other Stories or create crossovers
   Examples: "Connect this with my other story", "Bring characters from my fantasy story"

4. 'other': Anything that doesn't fit the above categories
   Examples: General chat, unclear requests, off-topic messages

User message: "{message}"

Respond with only the intent category (one word): query, modify, multiverse, or other
"""
    
    def classify(self, message: str) -> IntentType:
        try:
            prompt = self._classification_prompt.format(message=message)
            from app.core.concurrency import acquire_llm_thread_semaphore
            with acquire_llm_thread_semaphore():
                response = self.llm.invoke(prompt)
            intent_str = response.content.strip().lower()
            intent_mapping = {
                "query": IntentType.QUERY,
                "modify": IntentType.MODIFY,
                "multiverse": IntentType.MULTIVERSE,
                "other": IntentType.OTHER,
            }
            intent = intent_mapping.get(intent_str, IntentType.OTHER)
            logger.info(f"Classified intent as: {intent.value}")
            return intent
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            raise ChatbotError(f"Failed to classify user intent: {e}")


class VectorStoreManager:
    def __init__(self):
        self.vectorstore: Optional[PGVector] = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self) -> None:
        try:
            connection_string = settings.get_postgres_connection_string()
            embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            self.vectorstore = PGVector(
                embeddings=embeddings,
                connection=connection_string,
                collection_name=settings.VECTOR_COLLECTION_NAME,
                use_jsonb=True,
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise VectorStoreError(f"Vector store initialization failed: {e}")
    
    def get_retriever(self, story_id: str, k: int = None):
        if not self.vectorstore:
            raise VectorStoreError("Vector store not initialized")
        search_k = k or settings.VECTOR_SEARCH_K
        try:
            return self.vectorstore.as_retriever(
                search_kwargs={"k": search_k, "filter": {"story_id": story_id}}
            )
        except Exception as e:
            logger.error(f"Failed to create retriever: {e}")
            raise VectorStoreError(f"Retriever creation failed: {e}")


class StoryChatbot:
    def __init__(self):
        try:
            settings.validate_required_settings()
            self.llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
            )
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            self.memory_manager = MemoryManager()
            self.intent_classifier = IntentClassifier(self.llm)
            self.vector_manager = VectorStoreManager()
            logger.info("Story chatbot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize story chatbot: {e}")
            raise ChatbotError(f"Chatbot initialization failed: {e}")
    
    def chat(
        self,
        user_id: str,
        story_id: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Processing chat request - User: {user_id}, Story: {story_id}")
        try:
            if not self._validate_story_ownership(user_id, story_id):
                return ChatResponse(
                    type="error",
                    content="You do not have access to this story.",
                    metadata={"error_code": "UNAUTHORIZED"},
                ).__dict__
            intent = self.intent_classifier.classify(message)
            if intent == IntentType.QUERY:
                return self._handle_query(user_id, story_id, message)
            elif intent == IntentType.MODIFY:
                return self._handle_modify(user_id, story_id, message)
            elif intent == IntentType.MULTIVERSE:
                return self._handle_multiverse(user_id, story_id, message)
            else:
                return self._handle_unknown(message, intent)
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            logger.debug(traceback.format_exc())
            return ChatResponse(
                type="error",
                content="I encountered an error while processing your request. Please try again.",
                metadata={"error": str(e)},
            ).__dict__
    
    def _validate_story_ownership(self, user_id: str, story_id: str) -> bool:
        try:
            result = self.supabase.table("Stories").select("id").eq("id", story_id).eq("user_id", user_id).single().execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Story ownership validation failed: {e}")
            raise DatabaseConnectionError(f"Failed to validate story ownership: {e}")
    
    def _handle_query(self, user_id: str, story_id: str, message: str) -> Dict[str, Any]:
        logger.info(f"Handling story query for story {story_id}")
        try:
            retriever = self.vector_manager.get_retriever(story_id)
            memory = self.memory_manager.get_memory(user_id, story_id)
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=memory,
                return_source_documents=True,
                output_key="answer",
            )
            from app.core.concurrency import acquire_llm_thread_semaphore
            with acquire_llm_thread_semaphore():
                result = chain.invoke({"question": message})
            raw_sources = result.get("source_documents", [])
            unique_Chapters = {}
            for doc in raw_sources:
                metadata = doc.metadata
                chapter_id = metadata.get("chapter_id")
                chapter_number = metadata.get("chapter_number")
                unique_key = chapter_id or f"chapter_{chapter_number}"
                if unique_key not in unique_Chapters:
                    unique_Chapters[unique_key] = {
                        "chapter_id": chapter_id,
                        "chapter_number": chapter_number,
                        "chapter_title": metadata.get("chapter_title"),
                        "story_title": metadata.get("story_title"),
                        "story_id": metadata.get("story_id"),
                        "source_table": metadata.get("source_table"),
                    }
            sources = list(unique_Chapters.values())
            logger.info("Story query processed successfully")
            return ChatResponse(
                type="answer",
                content=result["answer"],
                intent=IntentType.QUERY.value,
                sources=sources,
            ).__dict__
        except Exception as e:
            logger.error(f"Query handling failed: {e}")
            return ChatResponse(
                type="error",
                content="I couldn't search your story right now. Please try again later.",
                metadata={"error": str(e)},
            ).__dict__
    
    def _handle_modify(self, user_id: str, story_id: str, message: str) -> Dict[str, Any]:
        logger.info(f"Handling story modification request for story {story_id}")
        return ChatResponse(
            type="modification_request",
            content=(
                "Story modification features are coming soon! I'll be able to help you rewrite Chapters, "
                "change character traits, modify plot elements, and more."
            ),
            intent=IntentType.MODIFY.value,
            status="pending",
            metadata={"feature_status": "in_development"},
        ).__dict__
    
    def _handle_multiverse(self, user_id: str, story_id: str, message: str) -> Dict[str, Any]:
        logger.info(f"Handling multiverse request for user {user_id}, story {story_id}")
        try:
            user_Stories = self.supabase.table("Stories").select("id,story_title").eq("user_id", user_id).execute()
            available_Stories = [s["story_title"] for s in user_Stories.data if str(s["id"]) != story_id]
            return ChatResponse(
                type="multiverse_request",
                content=(
                    f"You have {len(available_Stories)} other Stories available for multiverse connections. "
                    "Multiverse features are coming soon - I'll be able to help you create character crossovers, "
                    "shared universes, and connecting storylines!"
                ),
                intent=IntentType.MULTIVERSE.value,
                status="pending",
                metadata={
                    "available_Stories": available_Stories,
                    "total_Stories": len(user_Stories.data),
                    "feature_status": "in_development",
                },
            ).__dict__
        except Exception as e:
            logger.error(f"Multiverse handling failed: {e}")
            return ChatResponse(
                type="error",
                content="I couldn't access your other Stories right now. Please try again later.",
                metadata={"error": str(e)},
            ).__dict__
    
    def _handle_unknown(self, message: str, intent: IntentType) -> Dict[str, Any]:
        logger.info(f"Handling unknown intent: {intent.value}")
        return ChatResponse(
            type="unknown",
            content=(
                "I'm here to help you with your Stories! You can:\n\n"
                "• Ask questions about your story content\n"
                "• Request modifications to characters, plot, or Chapters\n"
                "• Create connections between your different Stories\n\n"
                "What would you like to do with your story?"
            ),
            intent=intent.value,
            metadata={"suggestions": ["query", "modify", "multiverse"]},
        ).__dict__


try:
    story_chatbot = StoryChatbot()
    logger.info("Global story chatbot instance created successfully")
except Exception as e:
    logger.error(f"Failed to create global chatbot instance: {e}")
    story_chatbot = None





