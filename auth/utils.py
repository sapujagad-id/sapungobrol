import os

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file, if present

def get_jwt_secret_key():
    return os.getenv("JWT_SECRET_KEY", "default_secret_key")  # Fallback to a default value if not set