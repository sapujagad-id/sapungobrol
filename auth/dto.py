from pydantic import BaseModel
from typing_extensions import TypedDict

from auth.user import User


class LoginResponse(BaseModel):
  access_token: str

class ProfileResponse(TypedDict):
  data: User

class GoogleCredentials(BaseModel):
  client_id: str
  client_secret: str
  redirect_uri: str