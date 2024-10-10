from abc import ABC, abstractmethod
import base64
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from loguru import logger
import requests

from auth.repository import AuthRepository
from auth.dto import GoogleCredentials, ProfileResponse
from auth.user import GoogleUserInfo
from jose import jwt


class AuthService(ABC):
    @abstractmethod
    def authorize_google(self, request: Request, user_info_json: GoogleUserInfo) -> Response:
      pass
    
    @abstractmethod
    def login_redirect_google(self) -> Response:
      pass
    
    @abstractmethod
    def get_user_profile(self, token: str) -> ProfileResponse:
      pass
  
class AuthServiceV1(AuthService):
    def __init__(self, repository: AuthRepository, google_credentials: GoogleCredentials, base_url: str) -> None:
      super().__init__()
      self.repository = repository
      self.google_credentials = google_credentials
      self.base_url = base_url
      self.logger = logger.bind(service="AuthService")
      