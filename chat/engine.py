from abc import ABC, abstractmethod


class ChatEngine(ABC):
    @abstractmethod
    def generate_response(self, query: str, context: str = None) -> str:
        """Generate a response based on the query and current session's context."""
        pass
