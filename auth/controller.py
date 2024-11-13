from abc import ABC, abstractmethod
from urllib.parse import urlencode
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError
from loguru import logger
import requests

from auth.dto import ProfileResponse
from auth.service import AuthService
from auth.user import GoogleUserInfo
from auth.exceptions import NoTokenSupplied, UserNotFound, UserUnauthorized
from config import AppConfig

class AuthController(ABC):
  @abstractmethod
  async def logout(self):
    pass
  
  @abstractmethod
  async def login_redirect_google(self) -> RedirectResponse:
    pass
  
  @abstractmethod
  async def authorize_google(self, request: Request, code: str) -> Response:
    pass

  @abstractmethod
  def get_all_users_basic_info(self, request: Request):
    pass
  
  @abstractmethod
  async def user_profile_google(self, request: Request) -> ProfileResponse:
    pass

class AuthControllerV1(AuthController):
  def __init__(self, service: AuthService) -> None:
    super().__init__() 
    self.service = service
    self.logger = logger.bind(service="AuthController")
    
  def logout(self) -> Response:
    response = RedirectResponse("/")
    try:
      response.delete_cookie("token")
    except:
      pass
    return response
    
  def login_redirect_google(self) -> Response:
    response = self.service.login_redirect_google()
    return response
    
  def authorize_google(self, request: Request, code: str) -> Response :
    response = self.service.authorize_google(request, code)

    return response
  
  def get_all_users_basic_info(self, request: Request):
    token = request.cookies.get("token")
    try:
      all_user = self.service.get_all_users_basic_info(token)
      return all_user
    except (NoTokenSupplied, UserUnauthorized):
      raise HTTPException(status_code=401, detail="You are not authenticated")
    except ExpiredSignatureError:
      raise HTTPException(status_code=400, detail="Your token has expired, please login again")    
    except JWTError:
      raise HTTPException(status_code=400, detail="Invalid token signature")
    except UserNotFound:
      raise HTTPException(status_code=404, detail="User not found")

  def user_profile_google(self, request: Request) -> ProfileResponse:
    token = request.cookies.get("token")
    try:
      user = self.service.get_user_profile(token)
      return ProfileResponse(
        data=user,
      )
    except NoTokenSupplied:
      raise HTTPException(status_code=401, detail="You are not authenticated")
    except ExpiredSignatureError:
      raise HTTPException(status_code=400, detail="Your token has expired, please login again")    
    except JWTError:
      raise HTTPException(status_code=400, detail="Invalid token signature")
    except UserNotFound:
      raise HTTPException(status_code=404, detail="User not found")