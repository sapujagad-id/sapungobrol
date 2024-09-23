import os
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None or DATABASE_URL == "":
    raise ValueError("database url is required")

db_engine = create_engine(DATABASE_URL)
SessionType = Session
DbSession = sessionmaker(bind=db_engine)
ModelBase = declarative_base()


def config_db(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url)
    return sessionmaker(bind=engine)


def get_db_session():
    db = DbSession()
    try:
        yield db
    finally:
        db.close()


class GroupModel(ModelBase):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class GroupCreate(BaseModel):
    name: str


class Group(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


def get_group(db: Session):
    return db.query(GroupModel).first()


# TODO: change this to alembic when actually building
ModelBase.metadata.create_all(bind=db_engine)
