"""
Custom exception classes for Bookology Backend.

This module defines custom exception classes used throughout the application
to provide better error handling and more specific error messages.
"""


class BookologyBaseException(Exception):
    """
    Base exception class for all Bookology-specific exceptions.
    
    This serves as the parent class for all custom exceptions in the application,
    allowing for easy exception handling and categorization.
    """
    
    def __init__(self, message: str, error_code: str = None):
        """
        Initialize the base exception.
        
        Args:
            message (str): Human-readable error message.
            error_code (str, optional): Machine-readable error code.
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(BookologyBaseException):
    """
    Raised when there's an issue with application configuration.
    
    This exception is raised when required environment variables are missing
    or when configuration validation fails.
    """
    pass


class DatabaseConnectionError(BookologyBaseException):
    """
    Raised when there's an issue connecting to the database.
    
    This exception is raised when database connections fail or when
    there are issues with database operations.
    """
    pass


class VectorStoreError(BookologyBaseException):
    """
    Raised when there's an issue with vector store operations.
    
    This exception is raised when vector store initialization fails
    or when there are issues with embedding operations.
    """
    pass


class ChatbotError(BookologyBaseException):
    """
    Raised when there's an issue with chatbot operations.
    
    This exception is raised when chatbot processing fails or when
    there are issues with LLM interactions.
    """
    pass


class AuthorizationError(BookologyBaseException):
    """
    Raised when there's an authorization issue.
    
    This exception is raised when users try to access resources
    they don't have permission to access.
    """
    pass


class StoryNotFoundError(BookologyBaseException):
    """
    Raised when a requested story is not found.
    
    This exception is raised when operations are attempted on
    Stories that don't exist or are not accessible.
    """
    pass


class GenerationError(BookologyBaseException):
    """
    Raised when there's an issue with content generation.
    
    This exception is raised when story generation, chapter creation,
    or other content generation processes fail.
    """
    pass