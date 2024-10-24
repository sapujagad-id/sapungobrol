from types import coroutine
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from unittest.mock import Mock
from jose import jwt
from bot.conftest import setup_jwt_secret
from config import AppConfig
from auth.middleware import login_required  # Adjust the import as needed
from fastapi.responses import JSONResponse

# Sample app to use for testing
app = FastAPI()

# Mock function to decorate
@app.get("/protected")
@login_required
async def protected_route(request: Request):
    return JSONResponse(content={"message": "You are logged in!"})

@pytest.fixture
def setup_app():
    return app

@pytest.fixture
def valid_token(setup_jwt_secret):
    # Generate a valid JWT token for testing
    return jwt.encode({"sub": "user_id"}, key="some_arbitrary_string_here", algorithm="HS256")

@pytest.fixture
def invalid_token(setup_jwt_secret):
    # Generate an invalid JWT token (e.g., altered or expired)
    return "invalid.token.string"

@pytest.mark.asyncio
async def test_login_required_valid_token(setup_app, valid_token, setup_jwt_secret):
    request = Mock(spec=Request)
    request.cookies = {"token": valid_token}

    response = await protected_route(request=request, jwt_secret_key=setup_jwt_secret)

    assert response

@pytest.mark.asyncio
async def test_login_required_no_token(setup_app):
    request = Mock(spec=Request)
    request.cookies = {}

    response = await protected_route(request=request)

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 302

@pytest.mark.asyncio
async def test_login_required_invalid_token(setup_app, invalid_token):
    request = Mock(spec=Request)
    request.cookies = {"token": invalid_token}

    response = await protected_route(request=request)

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 302
