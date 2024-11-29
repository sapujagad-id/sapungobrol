from unittest.mock import Mock
import pytest

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from uuid import uuid4


from .reaction_event_repository import (
    PostgresReactionEventRepository,
    ReactionEventModel,
)

TEST_DATABASE_URL = "sqlite:///:memory:"    

@pytest.fixture()
def setup_database():
    """Create a test database and tables."""
    engine = create_engine(TEST_DATABASE_URL)
    ReactionEventModel.metadata.create_all(engine)
    yield engine
    ReactionEventModel.metadata.drop_all(engine)

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
    repository = PostgresReactionEventRepository(session=lambda: session)
    return repository