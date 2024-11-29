import pytest
from fastapi import HTTPException
from uuid import uuid4

class TestReactionEventController:
    def test_get_reaction_event_by_chatbot_id_success(self, setup_controller, setup_service):
        """Test successful retrieval of reaction events."""
        bot_id = str(uuid4())
        mock_response = [
            {
                "total_conversations": 2,
                "average_negative_reactions_per_conversation": 1.0,
                "negative_reactions_per_conversation": [
                    {"conversation_id": "conv1", "negative_reactions": 2},
                    {"conversation_id": "conv2", "negative_reactions": 0},
                ],
            }
        ]
        setup_service.get_reaction_event_by_bot_id.return_value = mock_response

        result = setup_controller.get_reaction_event_by_chatbot_id(bot_id)

        setup_service.get_reaction_event_by_bot_id.assert_called_once_with(bot_id)
        assert result == mock_response

    def test_get_reaction_event_by_chatbot_id_service_error(self, setup_controller, setup_service):
        """Test handling of service-level exceptions."""
        bot_id = str(uuid4())
        setup_service.get_reaction_event_by_bot_id.side_effect = HTTPException(status_code=404, detail="Bot not found")

        with pytest.raises(HTTPException) as exc:
            setup_controller.get_reaction_event_by_chatbot_id(bot_id)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Bot not found"
        setup_service.get_reaction_event_by_bot_id.assert_called_once_with(bot_id)

    def test_get_reaction_event_by_chatbot_id_general_error(self, setup_controller, setup_service):
        """Test handling of general exceptions."""
        bot_id = str(uuid4())
        setup_service.get_reaction_event_by_bot_id.side_effect = HTTPException(status_code=500, detail=setup_controller.GENERAL_ERROR_MESSAGE)

        with pytest.raises(HTTPException) as exc:
            setup_controller.get_reaction_event_by_chatbot_id(bot_id)

        assert exc.value.status_code == 500
        assert exc.value.detail == setup_controller.GENERAL_ERROR_MESSAGE
        setup_service.get_reaction_event_by_bot_id.assert_called_once_with(bot_id)