import enum

from datetime import datetime
from pydantic import BaseModel, ConfigDict, UUID4


class NameIsRequired(Exception):
    pass


class SystemPromptIsRequired(Exception):
    pass


class UnsupportedModel(Exception):
    pass


class ModelEngine(str, enum.Enum):
    OPENAI = "OpenAI"


class MessageAdapter(str, enum.Enum):
    SLACK = "Slack"


class Bot(BaseModel):
    id: UUID4
    name: str
    system_prompt: str
    model: ModelEngine
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotCreate(BaseModel):
    name: str
    system_prompt: str
    model: str

    def validate(self):
        if len(self.name) == 0:
            raise NameIsRequired
        if len(self.system_prompt) == 0:
            raise SystemPromptIsRequired
        if self.model not in ModelEngine._value2member_map_:
            raise UnsupportedModel
