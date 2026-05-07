import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-insecure-key')
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///workouts.db')
        self.DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
