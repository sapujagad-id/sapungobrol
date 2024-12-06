from abc import ABC, abstractmethod

from chat.exceptions import ChatResponseGenerationError
from rag.retriever.retriever import Retriever


class ChatEngine(ABC):

    def __init__(self, retriever: Retriever):
        self.history = [self._get_generate_system()]
        self.retriever = retriever

    @abstractmethod
    def _get_generate_system(self) -> dict: # pragma: no cover
        """
        Returns the system message specific to the chat engine.

        This method should be implemented in the child classes to return a system message
        that is tailored to the specific behavior or configuration of the chat engine.

        Returns:
            dict: A dictionary representing the system message for the chat engine.
        """
        pass

    @abstractmethod
    def _api_call(self, full_input: str): # pragma: no cover
        """
        Makes the API call in the child classes.

        This method should be implemented to handle the specific API request, including
        passing the full input to the appropriate API and handling the response.

        Args:
            full_input (str): The input string to be passed to the API for processing.
        """
        pass

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

