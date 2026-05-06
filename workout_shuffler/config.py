import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-only-insecure-key')
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///workouts.db')
    DEBUG: bool = os.getenv('DEBUG', 'true').lower() == 'true'
