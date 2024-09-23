from http import HTTPStatus
from app.message.chatbot import ChatbotDto
from db import SessionType, get_db_session
from fastapi import Body, Depends, APIRouter, HTTPException
from app.api.service.chatbot import ChatbotService as service

router = APIRouter()

@router.get("/")
def get_chatbots(
    db: SessionType = Depends(get_db_session)
  ):
  resp = service.get_chatbots(db)
  return resp
  
@router.post("/")
def create_chatbot(
    body: ChatbotDto,
    db: SessionType = Depends(get_db_session),
  ):
  resp = service.create_chatbot(body, db)
  return resp

@router.get("/{id}")
def get_chatbot_detail(
    db: SessionType = Depends(get_db_session)
  ):
  # TODO
  raise HTTPException(status_code=HTTPStatus.NOT_IMPLEMENTED)
  
@router.patch("/{id}")
def edit_chatbot(
  db: SessionType = Depends(get_db_session)
):
  # TODO
  raise HTTPException(status_code=HTTPStatus.NOT_IMPLEMENTED)
  
@router.delete("/{id}")
def delete_chatbot(
  db: SessionType = Depends(get_db_session)
):
  # TODO
  raise HTTPException(status_code=HTTPStatus.NOT_IMPLEMENTED)
