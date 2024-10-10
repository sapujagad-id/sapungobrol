from datetime import datetime
import enum
import uuid
from pydantic import UUID4, BaseModel

class LoginMethod(str, enum.Enum):
  GOOGLE = "Google"

class User(BaseModel):
  id: UUID4
  sub: str
  name: str
  picture: str
  email: str
  email_verified: bool
  login_method: LoginMethod
  created_at: datetime
  
  def validate(self):
    if self.sub == "":
      pass
    if self.email == "":
      pass
    if self.name == "":
      pass
    if self.picture is not None and not self.picture.startswith("http"):
      pass
    if self.login_method not in LoginMethod._value2member_map_:
      pass
    if self.id == "":
      pass
  
class GoogleUserInfo(BaseModel):
  sub: str
  name: str
  given_name: str
  picture: str
  email: str
  email_verified: bool