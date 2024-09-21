from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_chatbots():
  return {
    "message": "OK!",
    "data": None,
  }
  
@router.post("/")
def create_chatbot():
  # TODO
  
  return {
    "message": "OK!",
    "data": None,
  }
  
@router.patch("/{id}")
def edit_chatbot():
  # TODO
  
  return {
    "message": "OK!",
    "data": None,
  }
  
@router.delete("/{id}")
def delete_chatbot():
  # TODO
  
  return {
    "message": "OK!",
    "data": None,
  }