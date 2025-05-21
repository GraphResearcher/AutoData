"""Custom exceptions for AutoData."""


class AutoDataError(Exception):
    """Base exception for all AutoData errors."""
    pass


class ConfigurationError(AutoDataError):
    """Raised when there is a configuration error."""
    pass


class LLMError(AutoDataError):
    """Raised when there is an error with the LLM service."""
    pass


class ExtractionError(AutoDataError):
    """Raised when there is an error during data extraction."""
    pass


class ValidationError(AutoDataError):
    """Raised when data validation fails."""
    pass


class AgentError(AutoDataError):
    """Raised when there is an error with an agent."""
    pass


class HTTPError(AutoDataError):
    """Raised when there is an HTTP-related error."""
    pass 