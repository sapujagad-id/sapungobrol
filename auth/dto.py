from pydantic import BaseModel

from auth.repository import UserModel
from auth.user import User

class LoginResponse(BaseModel):
  access_token: str

class ProfileResponse(BaseModel):
  data: User

class GoogleCredentials(BaseModel):
  client_id: str
  client_secret: str
  redirect_uri: str
  
class NoTokenSupplied(Exception):
  pass

class InvalidToken(Exception):
  pass

class UserNotFound(Exception):
  pass