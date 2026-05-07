import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-only-change-me')
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    _default_db = 'sqlite:////tmp/workouts.db' if os.getenv('VERCEL') else 'sqlite:///workouts.db'
    DATABASE_URL: str = os.getenv('DATABASE_URL', _default_db)
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
