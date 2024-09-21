from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.api.routes import api_router
from db import Group, get_db_session, get_group

app = FastAPI()

@app.get("/", response_model=Group | None)
def index(db: Session = Depends(get_db_session)):
    return get_group(db)

app.include_router(api_router)