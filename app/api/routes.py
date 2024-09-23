from fastapi import APIRouter

from app.api.controller import chatbot

api_router = APIRouter()
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])