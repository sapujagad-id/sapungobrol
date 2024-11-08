# Configurations for all tests in data_source module

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from auth.controller import AuthControllerV1
from auth.dto import ProfileResponse
from data_source.view import DataSourceViewV1

TEST_DATABASE_URL = "sqlite:///:memory:"  # Change as needed for your test setup

@pytest.fixture()
def session(setup_database):
    """Create a new database session for each test."""
    session_local = sessionmaker(
        bind=setup_database, 
        expire_on_commit=False
    )
    session = session_local()
    yield session
    session.close()

@pytest.fixture()
def setup_jwt_secret():
    """Set up a mock JWT secret."""
    return "some_arbitrary_secret_here"

@pytest.fixture()
def dummy_user_profile():
    """Return a mock user profile."""
    return ProfileResponse(data={
        "id": str(uuid4()),  # Replace with actual fields expected by User
        "email": "test@broom.id",
        "created_at": "2024-10-24T00:00:00Z",
        # Include other necessary fields...
    })

@pytest.fixture()
def setup_view():
    """Setup the BotViewV1 with mocked controller and service."""
    mock_controller = Mock(spec=AuthControllerV1)
    view = DataSourceViewV1(mock_controller)
    view.auth_controller = mock_controller
    return view