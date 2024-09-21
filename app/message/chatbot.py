from pydantic import BaseModel

class ChatbotDto(BaseModel):
  name: str
  system_prompt: str
  model: str
  data_source: str
  url: str
  tables: str