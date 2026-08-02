import os
from dotenv import load_dotenv

load_dotenv()  # reads values from .env file

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")

    DB_HOST     = os.getenv("DB_HOST", "localhost")
    DB_USER     = os.getenv("DB_USER", "studentuser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME     = os.getenv("DB_NAME", "studentdb")
