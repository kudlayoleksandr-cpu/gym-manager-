import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-insecure-key')
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        self.DATABASE_URL = self._resolve_database_url()
        self.DEBUG = self._resolve_debug()

    @staticmethod
    def _resolve_database_url() -> str:
        """Resolve database URL in priority order: DATABASE_URL, Vercel Postgres vars, then SQLite."""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            db_url = (
                os.getenv('POSTGRES_URL')
                or os.getenv('POSTGRES_URL_NON_POOLING')
                or os.getenv('POSTGRES_PRISMA_URL')
            )
        if not db_url:
            db_url = 'sqlite:////tmp/workouts.db' if Config._is_vercel_env() else 'sqlite:///workouts.db'
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url

    @staticmethod
    def _is_vercel_env() -> bool:
        return bool(os.getenv('VERCEL') or os.getenv('VERCEL_ENV'))

    @staticmethod
    def _resolve_debug() -> bool:
        default_debug = 'false' if Config._is_vercel_env() else 'true'
        return os.getenv('DEBUG', default_debug).lower() == 'true'
