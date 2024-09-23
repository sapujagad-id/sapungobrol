from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models.chatbot import Chatbot

class ChatbotRepository:
  def fetch_chatbots(db: Session):
    return db.query(Chatbot).all()
  
  def create_chatbot(chatbot, db: Session):
    try:
      db.add(chatbot)
      db.commit()
      return
    except IntegrityError as e:
        # print(e.orig)
        raise e.orig
    except SQLAlchemyError as e:
        # print(e.orig)
        raise e.orig