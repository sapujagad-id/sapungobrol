import enum

from datetime import datetime
from pydantic import BaseModel, ConfigDict, UUID4


class ModelEngine(enum.Enum):
    OPENAI = "OpenAI"


class MessageAdapter(enum.Enum):
    SLACK = "Slack"


class Bot(BaseModel):
    id: UUID4
    name: str
    system_prompt: str
    model: ModelEngine
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
