from uuid import uuid4

from .repository import UserModel
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

    def test_get_all_users_basic_info_success(self, setup_repository, session):
        user1 = UserModel(
            id=uuid4(),
            sub="user1-sub",
            name="User One",
            picture="https://user1.com/pic.png",
            email="user1@broom.id",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            access_level=1,
        )
        user2 = UserModel(
            id=uuid4(),
            sub="user2-sub",
            name="User Two",
            picture="https://user2.com/pic.png",
            email="user2@broom.id",
            email_verified=True,
            login_method=LoginMethod.GOOGLE,
            access_level=2,
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        users_basic_info = setup_repository.get_all_users_basic_info()

        assert isinstance(users_basic_info, list)
        assert len(users_basic_info) == 2

        for user_info in users_basic_info:
            assert set(user_info.keys()) == set(UserModel.USER_BASIC_INFO_FIELDS)
        
        user1_info = next(info for info in users_basic_info if info["email"] == "user1@broom.id")
        assert user1_info["name"] == "User One"
        assert user1_info["access_level"] == 1

        user2_info = next(info for info in users_basic_info if info["email"] == "user2@broom.id")
        assert user2_info["name"] == "User Two"
        assert user2_info["access_level"] == 2