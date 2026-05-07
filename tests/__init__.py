import sys
import os

# Add workout_shuffler to path before any project imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workout_shuffler')))

os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-tests')
os.environ.setdefault('GEMINI_API_KEY', 'fake-api-key')
