from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4
from loguru import logger
from sqlalchemy import Boolean, Column, DateTime, Enum, String, Uuid
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from auth.user import GoogleUserInfo, LoginMethod, User

Base = declarative_base()

class UserModel(Base):
    """
    A signed in user
    """

    __tablename__ = "users"

    id = Column(Uuid, primary_key=True)
    sub = Column(String(127), nullable=False)
    name = Column(String(127), nullable=False)
    picture = Column(String(255), nullable=False)
    email = Column(String(127), nullable=False)
    email_verified = Column(Boolean, nullable=False)
    login_method = Column(Enum(LoginMethod, validate_strings=True), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"User id:{self.id}"
    
class AuthRepository(ABC):
    @abstractmethod
    def find_user_by_sub(self, sub: str) -> UserModel | None:
        pass
    
    @abstractmethod
    def find_user_by_email(self, email: str) -> UserModel | None:
        pass
    
    @abstractmethod
    def add_google_user(self, user_info_json: GoogleUserInfo) -> None:
        pass


class PostgresAuthRepository(AuthRepository):
    def __init__(self, session: sessionmaker) -> None:
        self.create_session = session
        self.logger = logger.bind(service="PostgresAuthRepository")
        
    def find_user_by_sub(self, sub: str) -> UserModel | None:
        with self.create_session() as session:
            with self.logger.catch(
                message=f"User with sub: {sub} not found", 
                reraise=True,
            ):
                return session.query(UserModel).filter(UserModel.sub == sub).first()
            
    def find_user_by_email(self, email: str) -> UserModel | None:
        with self.create_session() as session:
            with self.logger.catch(
                message=f"User with email: {email} not found", 
                reraise=True,
            ):
                assert isinstance(session, Session) 
                return session.query(UserModel).filter(UserModel.email == email).first()
            
    def add_google_user(self, user_info_json: GoogleUserInfo) -> None:
        with self.create_session() as session:
            with self.logger.catch(message="create user error", reraise=True):
                assert isinstance(session, Session)
                user = UserModel(
                    id = uuid4(),
                    sub = user_info_json['sub'],
                    name = user_info_json['name'],
                    picture = user_info_json['picture'],
                    email = user_info_json['email'],
                    email_verified = user_info_json['email_verified'],
                    login_method = LoginMethod.GOOGLE,
                )
                session.add(user)
                session.commit()