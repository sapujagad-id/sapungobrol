import enum
from datetime import datetime

from pydantic import UUID4, BaseModel
from typing_extensions import TypedDict

from .exceptions import (InvalidEmail, InvalidName, InvalidPictureURL,
                         SubNotFound)


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
  access_level: int
  
  def validate(self):
    if not self.sub:
      raise SubNotFound()
    if not self.email:
      raise InvalidEmail()
    if not self.email.endswith("broom.id"):
      raise InvalidEmail("Email must be a Broom.id email")
    if not self.name:
      raise InvalidName()
    if self.picture is not None and not self.picture.startswith("http"):
      raise InvalidPictureURL()
    # if self.login_method not in LoginMethod._value2member_map_:
    #   raise InvalidLoginMethod()
    # if not self.id:
    #   raise InvalidUUID()
  
class GoogleUserInfo(TypedDict):
  sub: str
  name: str
  given_name: str
  picture: str
  email: str
  email_verified: bool