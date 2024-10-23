import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from .repository import PostgresAuthRepository, UserModel
from .user import GoogleUserInfo, LoginMethod

class TestAuthRepository:
    def test_find_user_by_sub_not_found(self, setup_repository):
        sub = "non-existent-sub"
        user = setup_repository.find_user_by_sub(sub)
        assert user is None

    def test_find_user_by_sub_success(self, setup_repository, session):
        # Insert a user into the session for testing
        sub = "test-sub"
        user = UserModel(
            id=uuid4(),
            sub=sub,
            name="Test User",
            picture="https://test.com/pic.png",
            email="testuser@broom.id",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
        )
        session.add(user)
        session.commit()

        # Test finding the user
        found_user = setup_repository.find_user_by_sub(sub)
        assert found_user is not None
        assert found_user.sub == sub
        assert found_user.email == "testuser@broom.id"

    def test_find_user_by_email_not_found(self, setup_repository):
        email = "non-existent@broom.id"
        user = setup_repository.find_user_by_email(email)
        assert user is None

    def test_find_user_by_email_success(self, setup_repository, session):
        # Insert a user into the session for testing
        email = "testuser@broom.id"
        user = UserModel(
            id=uuid4(),
            sub="test-sub",
            name="Test User",
            picture="https://test.com/pic.png",
            email=email,
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
        )
        session.add(user)
        session.commit()

        # Test finding the user
        found_user = setup_repository.find_user_by_email(email)
        assert found_user is not None
        assert found_user.email == email
        assert found_user.sub == "test-sub"

    def test_add_google_user_success(self, setup_repository, session):
        # Create GoogleUserInfo data
        user_info = GoogleUserInfo(
            sub="new-sub",
            name="New User",
            given_name="anewuser",
            picture="https://newuser.com/pic.png",
            email="newuser@broom.id",
            email_verified=True,
        )

        setup_repository.add_google_user(user_info)
        added_user = session.query(UserModel).filter(UserModel.sub == "new-sub").first()

        assert added_user is not None
        assert added_user.sub == "new-sub"
        assert added_user.email == "newuser@broom.id"
