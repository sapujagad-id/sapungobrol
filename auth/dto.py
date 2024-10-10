from pydantic import BaseModel
from auth.user import User

class LoginResponse(BaseModel):
  access_token: str

class ProfileResponse(BaseModel):
  data: User

class GoogleCredentials(BaseModel):
  client_id: str
  client_secret: str
  redirect_uri: str