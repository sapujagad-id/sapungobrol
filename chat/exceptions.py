class ChatResponseGenerationError(Exception):
    def __init__(self, message="Failed to generate response from the chatbot"):
        self.message = message
        super().__init__(self.message)
