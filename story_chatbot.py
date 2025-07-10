"""
Bookology Story Chatbot - AI-Powered Story Interaction System

This module provides an intelligent chatbot system that enables users to interact
with their Stories through natural language. The chatbot supports:

- Story content queries through Retrieval-Augmented Generation (RAG)
- Story modification requests and assistance
- Multiverse features for connecting different Stories
- Intent classification for routing different types of requests
- Per-user, per-story conversational memory

Architecture:
- LangChain for conversational AI and RAG pipelines
- OpenAI GPT models for language understanding and generation
- pgvector for semantic search over story content
- Supabase for data persistence and user management
- Memory management for context-aware conversations
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import traceback

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_postgres import PGVector
from supabase import create_client, Client

# Local imports
from config import settings
from logger_config import logger
from exceptions import (
    ChatbotError, AuthorizationError, StoryNotFoundError,
    VectorStoreError, DatabaseConnectionError
)


class IntentType(Enum):
    """Enumeration of supported user intent types."""
    
    QUERY = "query"           # Asking questions about story content
    MODIFY = "modify"         # Requesting story modifications
    MULTIVERSE = "multiverse" # Creating story connections
    OTHER = "other"           # Unclassified or unsupported intents


@dataclass
class ChatResponse:
    """Structured response from the chatbot."""
    
    type: str
    content: str
    intent: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryManager:
    """
    Manages conversational memory for user-story sessions.
    
    This class maintains separate conversation hiStories for each
    (user_id, story_id) combination, enabling context-aware responses
    across multiple interactions with the same story.
    """
    
    def __init__(self):
        """Initialize the memory manager with an empty memory store."""
        self._memories: Dict[str, ConversationBufferMemory] = {}
        logger.info("Memory manager initialized")
    
    def get_memory(self, user_id: str, story_id: str) -> ConversationBufferMemory:
        """
        Retrieve or create conversational memory for a user-story session.
        
        Args:
            user_id (str): Unique identifier for the user.
            story_id (str): Unique identifier for the story.
            
        Returns:
            ConversationBufferMemory: Memory instance for the session.
        """
        session_key = f"{user_id}:{story_id}"
        
        if session_key not in self._memories:
            self._memories[session_key] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            logger.info(f"Created new memory session for {session_key}")
        
        return self._memories[session_key]
    
    def clear_memory(self, user_id: str, story_id: str) -> None:
        """
        Clear conversational memory for a specific user-story session.
        
        Args:
            user_id (str): Unique identifier for the user.
            story_id (str): Unique identifier for the story.
        """
        session_key = f"{user_id}:{story_id}"
        if session_key in self._memories:
            del self._memories[session_key]
            logger.info(f"Cleared memory session for {session_key}")


class IntentClassifier:
    """
    Classifies user messages to determine appropriate response handling.
    
    This class uses an LLM to analyze user messages and categorize them
    into predefined intent types for proper routing and response generation.
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Initialize the intent classifier.
        
        Args:
            llm (ChatOpenAI): Language model for intent classification.
        """
        self.llm = llm
        self._classification_prompt = self._build_classification_prompt()
    
    def _build_classification_prompt(self) -> str:
        """
        Build the prompt template for intent classification.
        
        Returns:
            str: Formatted prompt template.
        """
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
        """
        Classify a user message into an intent type.
        
        Args:
            message (str): User's message to classify.
            
        Returns:
            IntentType: Classified intent type.
            
        Raises:
            ChatbotError: If classification fails.
        """
        try:
            prompt = self._classification_prompt.format(message=message)
            response = self.llm.invoke(prompt)
            intent_str = response.content.strip().lower()
            
            # Map string response to enum
            intent_mapping = {
                "query": IntentType.QUERY,
                "modify": IntentType.MODIFY,
                "multiverse": IntentType.MULTIVERSE,
                "other": IntentType.OTHER
            }
            
            intent = intent_mapping.get(intent_str, IntentType.OTHER)
            logger.info(f"Classified intent as: {intent.value}")
            return intent
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            raise ChatbotError(f"Failed to classify user intent: {e}")


class VectorStoreManager:
    """
    Manages vector store operations for story content retrieval.
    
    This class handles the initialization and management of the pgvector
    store used for semantic search over story content.
    """
    
    def __init__(self):
        """Initialize the vector store manager."""
        self.vectorstore: Optional[PGVector] = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self) -> None:
        """
        Initialize the pgvector store with proper configuration.
        
        Raises:
            VectorStoreError: If initialization fails.
        """
        try:
            connection_string = settings.get_postgres_connection_string()
            embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            
            self.vectorstore = PGVector(
                embeddings=embeddings,
                connection=connection_string,
                collection_name=settings.VECTOR_COLLECTION_NAME,
                use_jsonb=True
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise VectorStoreError(f"Vector store initialization failed: {e}")
    
    def get_retriever(self, story_id: str, k: int = None):
        """
        Get a retriever configured for a specific story.
        
        Args:
            story_id (str): ID of the story to retrieve content for.
            k (int, optional): Number of documents to retrieve.
            
        Returns:
            Retriever: Configured retriever instance.
            
        Raises:
            VectorStoreError: If retriever creation fails.
        """
        if not self.vectorstore:
            raise VectorStoreError("Vector store not initialized")
        
        search_k = k or settings.VECTOR_SEARCH_K
        
        try:
            return self.vectorstore.as_retriever(
                search_kwargs={
                    "k": search_k,
                    "filter": {"story_id": story_id}
                }
            )
        except Exception as e:
            logger.error(f"Failed to create retriever: {e}")
            raise VectorStoreError(f"Retriever creation failed: {e}")


class StoryChatbot:
    """
    Main chatbot class for story interactions.
    
    This class orchestrates all chatbot functionality including intent
    classification, memory management, and response generation for
    different types of user requests.
    """
    
    def __init__(self):
        """Initialize the story chatbot with all required components."""
        try:
            # Validate configuration
            settings.validate_required_settings()
            
            # Initialize core components
            self.llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )
            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            
            # Initialize managers
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
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate an appropriate response.
        
        This is the main entry point for chat interactions. It handles
        authentication, intent classification, and routes requests to
        appropriate handlers.
        
        Args:
            user_id (str): ID of the user sending the message.
            story_id (str): ID of the story being discussed.
            message (str): User's message content.
            session_id (str, optional): Session identifier (unused currently).
            
        Returns:
            Dict[str, Any]: Chatbot response with type, content, and metadata.
        """
        logger.info(f"Processing chat request - User: {user_id}, Story: {story_id}")
        
        try:
            # Validate user owns the story
            if not self._validate_story_ownership(user_id, story_id):
                return ChatResponse(
                    type="error",
                    content="You do not have access to this story.",
                    metadata={"error_code": "UNAUTHORIZED"}
                ).__dict__
            
            # Classify user intent
            intent = self.intent_classifier.classify(message)
            
            # Route to appropriate handler
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
                metadata={"error": str(e)}
            ).__dict__
    
    def _validate_story_ownership(self, user_id: str, story_id: str) -> bool:
        """
        Validate that a user owns a specific story.
        
        Args:
            user_id (str): ID of the user.
            story_id (str): ID of the story.
            
        Returns:
            bool: True if user owns the story, False otherwise.
            
        Raises:
            DatabaseConnectionError: If database query fails.
        """
        try:
            result = self.supabase.table("Stories").select("id").eq(
                "id", story_id
            ).eq("user_id", user_id).single().execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Story ownership validation failed: {e}")
            raise DatabaseConnectionError(f"Failed to validate story ownership: {e}")
    
    def _handle_query(self, user_id: str, story_id: str, message: str) -> Dict[str, Any]:
        """
        Handle story content queries using RAG.
        
        Args:
            user_id (str): User ID.
            story_id (str): Story ID.
            message (str): User's query message.
            
        Returns:
            Dict[str, Any]: Query response with answer and sources.
        """
        logger.info(f"Handling story query for story {story_id}")
        
        try:
            # Get retriever for the story
            retriever = self.vector_manager.get_retriever(story_id)
            
            # Get conversational memory
            memory = self.memory_manager.get_memory(user_id, story_id)
            
            # Create conversational retrieval chain
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=memory,
                return_source_documents=True,
                output_key="answer"
            )
            
            # Process the query
            result = chain.invoke({"question": message})
            
            # Extract unique chapter sources (not individual chunks)
            raw_sources = result.get("source_documents", [])
            unique_Chapters = {}
            
            for doc in raw_sources:
                metadata = doc.metadata
                chapter_id = metadata.get("chapter_id")
                chapter_number = metadata.get("chapter_number")
                
                # Use chapter_id as unique key, or fallback to chapter_number
                unique_key = chapter_id or f"chapter_{chapter_number}"
                
                if unique_key not in unique_Chapters:
                    unique_Chapters[unique_key] = {
                        "chapter_id": chapter_id,
                        "chapter_number": chapter_number,
                        "chapter_title": metadata.get("chapter_title"),
                        "story_title": metadata.get("story_title"),
                        "story_id": metadata.get("story_id"),
                        "source_table": metadata.get("source_table")
                    }
            
            # Convert to list of unique chapter sources
            sources = list(unique_Chapters.values())
            
            logger.info("Story query processed successfully")
            
            return ChatResponse(
                type="answer",
                content=result["answer"],
                intent=IntentType.QUERY.value,
                sources=sources
            ).__dict__
            
        except Exception as e:
            logger.error(f"Query handling failed: {e}")
            return ChatResponse(
                type="error",
                content="I couldn't search your story right now. Please try again later.",
                metadata={"error": str(e)}
            ).__dict__
    
    def _handle_modify(self, user_id: str, story_id: str, message: str) -> Dict[str, Any]:
        """
        Handle story modification requests.
        
        Args:
            user_id (str): User ID.
            story_id (str): Story ID.
            message (str): User's modification request.
            
        Returns:
            Dict[str, Any]: Modification response.
        """
        logger.info(f"Handling story modification request for story {story_id}")
        
        # TODO: Implement story modification functionality
        # This would involve:
        # 1. Analyzing the modification request
        # 2. Generating new content based on the request
        # 3. Updating the story content in the database
        # 4. Re-generating embeddings for modified content
        
        return ChatResponse(
            type="modification_request",
            content="Story modification features are coming soon! I'll be able to help you rewrite Chapters, change character traits, modify plot elements, and more.",
            intent=IntentType.MODIFY.value,
            status="pending",
            metadata={"feature_status": "in_development"}
        ).__dict__
    
    def _handle_multiverse(self, user_id: str, story_id: str, message: str) -> Dict[str, Any]:
        """
        Handle multiverse connection requests.
        
        Args:
            user_id (str): User ID.
            story_id (str): Story ID.
            message (str): User's multiverse request.
            
        Returns:
            Dict[str, Any]: Multiverse response.
        """
        logger.info(f"Handling multiverse request for user {user_id}, story {story_id}")
        
        try:
            # Get user's other Stories
            user_Stories = self.supabase.table("Stories").select(
                "id,story_title"
            ).eq("user_id", user_id).execute()
            
            available_Stories = [
                story["story_title"] for story in user_Stories.data
                if str(story["id"]) != story_id
            ]
            
            # TODO: Implement multiverse functionality
            # This would involve:
            # 1. Analyzing cross-story connections
            # 2. Identifying compatible characters/elements
            # 3. Generating connecting narratives
            # 4. Updating story databases with connections
            
            return ChatResponse(
                type="multiverse_request",
                content=f"You have {len(available_Stories)} other Stories available for multiverse connections. Multiverse features are coming soon - I'll be able to help you create character crossovers, shared universes, and connecting storylines!",
                intent=IntentType.MULTIVERSE.value,
                status="pending",
                metadata={
                    "available_Stories": available_Stories,
                    "total_Stories": len(user_Stories.data),
                    "feature_status": "in_development"
                }
            ).__dict__
            
        except Exception as e:
            logger.error(f"Multiverse handling failed: {e}")
            return ChatResponse(
                type="error",
                content="I couldn't access your other Stories right now. Please try again later.",
                metadata={"error": str(e)}
            ).__dict__
    
    def _handle_unknown(self, message: str, intent: IntentType) -> Dict[str, Any]:
        """
        Handle unclassified or unsupported requests.
        
        Args:
            message (str): User's message.
            intent (IntentType): Classified intent type.
            
        Returns:
            Dict[str, Any]: Helpful response for unknown intents.
        """
        logger.info(f"Handling unknown intent: {intent.value}")
        
        return ChatResponse(
            type="unknown",
            content="I'm here to help you with your Stories! You can:\n\n"
                   "• Ask questions about your story content\n"
                   "• Request modifications to characters, plot, or Chapters\n"
                   "• Create connections between your different Stories\n\n"
                   "What would you like to do with your story?",
            intent=intent.value,
            metadata={"suggestions": ["query", "modify", "multiverse"]}
        ).__dict__


# Global chatbot instance
try:
    story_chatbot = StoryChatbot()
    logger.info("Global story chatbot instance created successfully")
except Exception as e:
    logger.error(f"Failed to create global chatbot instance: {e}")
    # Create a fallback instance that will handle errors gracefully
    story_chatbot = None