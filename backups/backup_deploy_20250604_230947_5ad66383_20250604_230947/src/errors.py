# Custom error classes for unified error handling

class ExternalAPIError(Exception):
    """Raised when an external API fails."""
    def __init__(self, service, message, *args):
        super().__init__(f"[{service}] {message}", *args)
        self.service = service

class TransientError(Exception):
    """Raised for errors that may succeed if retried."""
    pass

class PermanentError(Exception):
    """Raised for errors that should not be retried."""
    pass

class GracefulDegradation(Exception):
    """Raised when the system falls back to a degraded (but functional) state."""
    pass
