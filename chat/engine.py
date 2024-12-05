from abc import ABC, abstractmethod

from chat.exceptions import ChatResponseGenerationError
from rag.retriever.retriever import Retriever


class ChatEngine(ABC):

    def __init__(self, retriever: Retriever):
        self.history = [self._get_generate_system()]
        self.retriever = retriever

    @abstractmethod
    def _get_generate_system(self) -> dict:
        """Return the system message specific to the chat engine."""

    @abstractmethod
    def _api_call(self, full_input: str):
        """Abstract method for making the API call in the child classes."""

    def retrieve(self, query: str, access_level: int):
        return self.retriever.query(query, access_level)

    def generate_response(self, query: str, access_level: int = 1) -> str:
        if not query:
            return ""
        
        if not access_level or access_level < 1:
            access_level = 1
        
        context = self.retrieve(query, access_level)
        full_input = f"Given a context: {context}\n Given a query: {query}\n Please answer query based on the given context." if context else query

        self.add_chat_history("user", full_input)

        try:
            assistant_response = self._api_call(full_input)
            self.add_chat_history("assistant", assistant_response)
            return assistant_response
        except Exception as e:
            raise ChatResponseGenerationError(f"Error generating response: {str(e)}")

    def reset_history(self):
        """Reset the chat history."""
        self.history = [self._get_generate_system()]
        
    def add_chat_history(self, role, content):
        """Add chat history."""
        self.history.append({"role" : role, "content" : content})

