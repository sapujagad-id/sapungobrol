from pydantic import ValidationError
import pytest
from auth.user import LoginMethod, User
from .exceptions import SubNotFound, InvalidEmail, InvalidName, InvalidPictureURL
from uuid import uuid4
from datetime import datetime

# Tests

class TestUserValidation:
    def test_empty_sub(self):
        request = User(
            id=uuid4(),
            sub="",
            name="Seorang",
            picture="https://example.com/profile.jpg",
            email="manusia@gmail.com",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now()
        )
        with pytest.raises(SubNotFound):
            request.validate()

    def test_empty_email(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="Seorang",
            picture="https://example.com/profile.jpg",
            email="",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now()
        )
        with pytest.raises(InvalidEmail):
            request.validate()

    def test_empty_name(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="",
            picture="https://example.com/profile.jpg",
            email="manusia@gmail.com",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now()
        )
        with pytest.raises(InvalidName):
            request.validate()

    def test_invalid_picture_url(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="Seorang",
            picture="invalid_url",
            email="manusia@gmail.com",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now()
        )
        with pytest.raises(InvalidPictureURL):
            request.validate()

    def test_invalid_login_method(self):
        with pytest.raises(ValidationError):
            User(
                id=uuid4(),
                sub="some_sub",
                name="Seorang",
                picture="https://example.com/profile.jpg",
                email="manusia@gmail.com",
                email_verified=True,
                login_method="INVALID_METHOD",
                created_at=datetime.now()
            )

    def test_empty_id(self):
        with pytest.raises(ValidationError):
            User(
                id=None,
                sub="some_sub",
                name="Seorang",
                picture="https://example.com/profile.jpg",
                email="manusia@gmail.com",
                email_verified=True,
                login_method=LoginMethod.GOOGLE,
                created_at=datetime.now()
            )          

    def test_valid_user(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="Seorang",
            picture="https://example.com/profile.jpg",
            email="manusia@gmail.com",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now()
        )
        # Should not raise any exception
        request.validate()
