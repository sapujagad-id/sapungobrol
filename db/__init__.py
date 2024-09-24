from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def config_db(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url)
    return sessionmaker(bind=engine)
