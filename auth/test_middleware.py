import pytest
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from unittest.mock import Mock
from auth.conftest import setup_controller, setup_jwt_secret
from auth.middleware import login_required
import bot
import bot.conftest
from bot.view import BotViewV1


@pytest.fixture()
def setup_bot_view(setup_service):
    """Setup the BotViewV1 with mocked controller and service."""
    view = BotViewV1(bot.conftest.setup_service, bot.conftest.setup_controller, setup_controller)
    
    return view

class TestLoginRequired:
    
    @pytest.mark.asyncio
    async def test_login_required_valid_token(self, setup_bot_view, valid_token):
        request = Mock(spec=Request)
        request.cookies = {"token": valid_token}
        response = await setup_bot_view.show_list_chatbots(request=request)

        assert response

    @pytest.mark.asyncio
    async def test_login_required_no_token(self, setup_bot_view):
        request = Mock(spec=Request)
        request.cookies = {}

        response = await setup_bot_view.show_list_chatbots(request=request)

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302

    @pytest.mark.asyncio
    async def test_login_required_invalid_token(self, invalid_token, setup_bot_view):
        request = Mock(spec=Request)
        request.cookies = {"token": invalid_token}

        response = await setup_bot_view.show_list_chatbots(request=request)
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302