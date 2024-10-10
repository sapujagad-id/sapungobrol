from unittest.mock import Mock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.controller import AuthControllerV1
from auth.dto import GoogleCredentials
from auth.repository import PostgresAuthRepository, UserModel
from auth.service import AuthServiceV1

TEST_DATABASE_URL = "sqlite:///:memory:"  # Change as needed for your test setu

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
def setup_repository(session):
    """Set up the repository with the test session."""
    repository = PostgresAuthRepository(session=lambda: session)
    return repository
  
@pytest.fixture()
def setup_google_credentials():
  return GoogleCredentials(
    client_id="xxx",
    client_secret="xxx",
    redirect_uri="http://localhost:8000/api/auth/callback/google",
  )

@pytest.fixture()
def setup_service(setup_repository, setup_google_credentials):
    """Set up the service with the repository."""
    return Mock(spec=AuthServiceV1)
    # service = AuthServiceV1(
    #   setup_repository,
    #   setup_google_credentials,
    #   "http://localhost:8000",
    #   )
    # return service

@pytest.fixture()
def setup_controller(setup_service):
    """Set up the controller with the service."""
    controller = AuthControllerV1(setup_service)
    return controller

@pytest.fixture()
def setup_database():
    """Create a test database and tables."""
    engine = create_engine(TEST_DATABASE_URL)
    UserModel.metadata.create_all(engine)
    yield engine
    UserModel.metadata.drop_all(engine)
