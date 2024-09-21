from datetime import datetime
import enum
from sqlalchemy import Column, Enum, Uuid, String, Integer, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
  
class ModelEngine(enum.Enum):
  OPENAI = "OpenAI"
  ANTHROPIC = "Anthropic"
  
class MessageAdapter(enum.Enum):
  SLACK = "Slack"
  
class DataType(enum.Enum):
  SQL = "SQL"
  
class Chatbot(Base):
  '''
  A chatbot instance.
  '''
  __tablename__ = "chatbot"
  
  id = Column(Uuid, primary_key=True)
  name = Column(String(255), nullable=False)
  system_prompt = Column(Text(length=2048), nullable=False)
  model = Column(Enum(ModelEngine), nullable=False)
  data_source = Column(Enum(DataType), nullable=False)
  created_at = Column(DateTime, default=datetime.now)
  updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
  
  # required fields for SQL Data Type
  url = Column(String(127))
  tables = Column(String(255))
  
  def __repr__(self):
    return f"Chatbot id:{self.id}"
  
  