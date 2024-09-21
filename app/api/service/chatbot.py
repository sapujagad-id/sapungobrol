from http import HTTPStatus
import uuid

from fastapi import HTTPException
from app.api.repository.chatbot import ChatbotRepository
from app.message.chatbot import ChatbotDto
from app.models.chatbot import Chatbot, ModelEngine, DataType
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

class ChatbotService:
  def get_chatbots(db):
    try:
      data = ChatbotRepository.fetch_chatbots(db)
    except Exception as e:
      raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
    
    return {
      "message": "OK",
      "data": data,
    }

  def create_chatbot(dto: ChatbotDto, db):
    id = uuid.uuid4()
    try:
      model = ModelEngine(dto.model)
    except:
      raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid model")
    
    try:
      data_source = DataType(dto.data_source)
    except:
      raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid data source")
    
    chatbot = Chatbot(
      id = id,
      name = dto.name,
      system_prompt = dto.system_prompt,
      model = model,
      data_source = data_source,
      url = dto.url,
      tables = dto.tables,
    )
    
    try:
      ChatbotRepository.create_chatbot(chatbot, db)
    except Exception as err:
      raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=err.__str__())
    return {
      "message": "Chatbot successfully created",
      "data": chatbot,
    }