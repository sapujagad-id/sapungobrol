import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from uuid import uuid4
from adapter.reaction_event import Reaction, ReactionEventCreate
from adapter.reaction_event_service import ReactionEventService
from bot.bot import MessageAdapter

class TestReactionEventService:
    def test_get_reaction_event_by_chatbot_id_success(self, setup_controller, setup_real_service, setup_repository):
        """Test successful retrieval of reaction events."""
        setup_service = setup_real_service
        bot_id = uuid4()
        reaction_event_create = ReactionEventCreate(
            bot_id=bot_id,
            reaction=Reaction.NEGATIVE,
            source_adapter=MessageAdapter.SLACK,
            source_adapter_message_id="123456.7890",
            source_adapter_user_id="U1234567890",
            message="Hi there!",
        )

        setup_repository.create_reaction_event(reaction_event_create)
        

        result = setup_service.get_reaction_event_by_bot_id(bot_id)
        assert result.get("total_conversations") == 1
        assert result.get("average_negative_reactions_per_conversation") == 1

    def test_get_reaction_event_by_chatbot_id_service_error(self, setup_controller, setup_real_service):
        """Test handling of service-level exceptions."""
        setup_service = setup_real_service
        bot_id = uuid4()

        with pytest.raises(HTTPException) as exc:
            setup_service.get_reaction_event_by_bot_id(bot_id)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Reaction not found"

    def test_get_reaction_event_by_chatbot_id_general_error(self, setup_controller, setup_real_service):
        """Test handling of general exceptions."""
        setup_service = setup_real_service
        bot_id = str(uuid4())

        with pytest.raises(HTTPException) as exc:
            setup_service.get_reaction_event_by_bot_id(bot_id)

        assert exc.value.status_code == 500