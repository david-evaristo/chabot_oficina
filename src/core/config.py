import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///mech_ai.db')

    # Google Sheets configuration
    SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
    SHEETS_TAB_NAME = os.getenv("SHEETS_TAB_NAME", "Registros")
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")