from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from auth.user import LoginMethod, User

from .exceptions import (InvalidEmail, InvalidName, InvalidPictureURL,
                         SubNotFound)

# Tests

class TestUserValidation:
    def test_empty_sub(self):
        request = User(
            id=uuid4(),
            sub="",
            name="Seorang",
            picture="https://example.com/profile.jpg",
            email="manusia@broom.id",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now(),
            access_level=0
        )
        with pytest.raises(SubNotFound):
            request.validate()
            
    def test_non_broom_email(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="Seorang",
            picture="https://example.com/profile.jpg",
            email="me@gmail.com",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now(),
            access_level=0

        )
        with pytest.raises(InvalidEmail):
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
            created_at=datetime.now(),
            access_level=0

        )
        with pytest.raises(InvalidEmail):
            request.validate()

    def test_empty_name(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="",
            picture="https://example.com/profile.jpg",
            email="manusia@broom.id",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now(),
            access_level=0

        )
        with pytest.raises(InvalidName):
            request.validate()

    def test_invalid_picture_url(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="Seorang",
            picture="invalid_url",
            email="manusia@broom.id",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now(),
            access_level=0,
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
                email="manusia@broom.id",
                email_verified=True,
                login_method="INVALID_METHOD",
                created_at=datetime.now(),
                access_level=0

            )

    def test_empty_id(self):
        with pytest.raises(ValidationError):
            User(
                id=None,
                sub="some_sub",
                name="Seorang",
                picture="https://example.com/profile.jpg",
                email="manusia@broom.id",
                email_verified=True,
                login_method=LoginMethod.GOOGLE,
                created_at=datetime.now(),
                access_level=0

            )          

    def test_valid_user(self):
        request = User(
            id=uuid4(),
            sub="some_sub",
            name="Seorang",
            picture="https://example.com/profile.jpg",
            email="manusia@broom.id",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            created_at=datetime.now(),
            access_level=0
        )
        # Should not raise any exception
        request.validate()
