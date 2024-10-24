from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from functools import wraps
from loguru import logger
from jose import jwt
from config import AppConfig

def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pass
    
    return wrapper
