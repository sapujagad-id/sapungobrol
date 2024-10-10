import enum

from datetime import datetime
from pydantic import BaseModel, ConfigDict, UUID4
from typing import Optional


class NameIsRequired(Exception):
    pass

class BotNotFound(Exception):
    pass

class SystemPromptIsRequired(Exception):
    pass

class UnsupportedModel(Exception):
    pass

class UnsupportedAdapter(Exception):
    pass

class SlugIsRequired(Exception):
    pass


class ModelEngine(str, enum.Enum):
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"


class MessageAdapter(str, enum.Enum):
    SLACK = "Slack"


class Bot(BaseModel):
    id: UUID4
    name: str
    system_prompt: str
    model: ModelEngine
    created_at: datetime
    updated_at: datetime
    adapter: MessageAdapter
    slug: str

    model_config = ConfigDict(from_attributes=True)
    
class BotResponse(Bot):
    updated_at_relative: str

class BotCreate(BaseModel):
    name: str
    system_prompt: str
    model: str
    adapter: str
    slug: str

    def validate(self):
        if self.adapter not in MessageAdapter._value2member_map_:
            raise UnsupportedAdapter
        if len(self.name) == 0:
            raise NameIsRequired
        if len(self.system_prompt) == 0:
            raise SystemPromptIsRequired
        if len(self.slug) == 0:
            raise SlugIsRequired
        if self.model not in ModelEngine._value2member_map_:
            raise UnsupportedModel
        
class BotUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    adapter: Optional[str] = None
    slug: Optional[str] = None

    def validate(self, bot):
        if self.adapter and self.adapter not in MessageAdapter._value2member_map_:
            raise UnsupportedAdapter
        if self.name is not None and len(self.name) == 0:
            raise NameIsRequired
        if self.system_prompt is not None and len(self.system_prompt) == 0:
            raise SystemPromptIsRequired
        if self.slug is not None and len(self.slug) == 0:
            raise SlugIsRequired
        if self.model and self.model not in ModelEngine._value2member_map_:
            raise UnsupportedModel
        if not bot:
            raise BotNotFound
