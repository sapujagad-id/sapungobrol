from .bot import BotCreate, NameIsRequired, SystemPromptIsRequired, UnsupportedAdapter, UnsupportedModel

import pytest


class TestBotCreate:
    def test_empty_name(self):
        request = BotCreate(
            name="",
            system_prompt="Non-empty prompt",
            model="OpenAI",
            adapter="Slack"
        )
        with pytest.raises(NameIsRequired):
            request.validate()

    def test_empty_system_prompt(self):
        request = BotCreate(
            name="Customer Report", 
            system_prompt="",
            model="OpenAI",
            adapter="Slack"
        )
        with pytest.raises(SystemPromptIsRequired):
            request.validate()
            
    def test_unsupported_model(self):
        request = BotCreate(
            name="Customer Report", 
            system_prompt="Non-empty prompt", 
            adapter="Slack",
            model="ClosedAI"
        )

        with pytest.raises(UnsupportedModel):
            request.validate()
    
    def test_unsupported_adapter(self):
        request = BotCreate(
            name="Customer Report", 
            system_prompt="Non-empty prompt", 
            adapter="WeChatV2",
            model="OpenAI"
        )

        with pytest.raises(UnsupportedAdapter):
            request.validate()

    def test_create_bot_ok(self):
        tests = [
            {
                "name": "Customer Service",
                "system_prompt": "Non-empty prompt",
                "adapter": "Slack",
                "model": "OpenAI",
            },
        ]

        for test in tests:
            request = BotCreate(**test)
            request.validate()
