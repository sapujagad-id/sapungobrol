from abc import ABC, abstractmethod
from urllib.parse import urlencode
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError
from loguru import logger
import requests

from auth.service import AuthService
from auth.user import GoogleUserInfo
from auth.exceptions import NoTokenSupplied, UserNotFound
from config import AppConfig

class AuthController(ABC):
  @abstractmethod
  async def logout():
    pass
  
  @abstractmethod
  async def login_redirect_google():
    pass
  
  @abstractmethod
  async def authorize_google(code: str):
    pass
  
  @abstractmethod
  async def user_profile_google(token: str):
    pass

class AuthControllerV1(AuthController):
  def __init__(self, service: AuthService) -> None:
    super().__init__() 
    self.service = service
    self.logger = logger.bind(service="AuthController")
    
  def logout(self, request: Request):
    response = RedirectResponse("/")
    response.delete_cookie("token")
    return response
    
  def login_redirect_google(self):
    response = self.service.login_redirect_google()
    return response
    
  def authorize_google(self, request: Request, code: str):
    response = self.service.authorize_google(request, code)

    return response

  def user_profile_google(self, request: Request):
    token = request.cookies.get("token")
    try:
      response = self.service.get_user_profile(token)
    except NoTokenSupplied:
      raise HTTPException(status_code=401, detail="You are not authenticated")
    except JWTError:
      raise HTTPException(status_code=400, detail="Invalid token signature")
    except ExpiredSignatureError:
      raise HTTPException(status_code=400, detail="Your token has expired, please login again")
    except UserNotFound:
      raise HTTPException(status_code=404, detail="User not found")
    return response