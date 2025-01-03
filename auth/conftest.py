from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.controller import AuthControllerV1
from auth.dto import GoogleCredentials
from auth.middleware import AuthMiddleware
from auth.repository import PostgresAuthRepository, UserModel
from auth.service import AuthServiceV1

TEST_DATABASE_URL = "sqlite:///:memory:"  # Change as needed for your test setu


@pytest.fixture()
def session(setup_database):
    """Create a new database session for each test."""
    session_local = sessionmaker(bind=setup_database, expire_on_commit=False)
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
def setup_service():
    """Set up a mocked service."""
    service = Mock(spec=AuthServiceV1)
    service.repository = Mock(spec=PostgresAuthRepository)

    return service


@pytest.fixture()
def setup_jwt_secret():
    """Set up JWT secret for AuthService"""
    return "some_arbitrary_string_here"


@pytest.fixture()
def setup_real_service(setup_repository, setup_google_credentials, setup_jwt_secret):
    """Set up the REAL service with the repository."""
    service = AuthServiceV1(
        setup_repository,
        setup_google_credentials,
        "http://localhost:8000",
        setup_jwt_secret,
        "example@broom.id",
        5,
    )
    return service


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


@pytest.fixture
def valid_token(setup_jwt_secret):
    # Generate a valid JWT token for testing
    return jwt.encode({"sub": "user_id"}, key=setup_jwt_secret, algorithm="HS256")


@pytest.fixture
def invalid_token(setup_jwt_secret):
    # Generate an invalid JWT token (e.g., altered or expired)
    return "invalid.token.string"


@pytest.fixture
def app(setup_jwt_secret):
    app = FastAPI()

    @app.get("/public")
    async def public_endpoint():
        return {"message": "Public"}

    @app.get("/private")
    async def private_endpoint():
        return {"message": "Private"}

    @app.get("/dynamic/{id}")
    async def dynamic_endpoint(id: str):
        return {"id": id}

    @app.get("/login")
    async def login_endpoint():
        return {"message": "Login"}

    included_routes = ["/private", "/dynamic/*", "/private-curly/{id}"]
    app.add_middleware(
        AuthMiddleware,
        jwt_secret_key=setup_jwt_secret,
        login_url="/login",
        included_routes=included_routes,
    )
    return app


@pytest.fixture
def client(app):
    return TestClient(app)
