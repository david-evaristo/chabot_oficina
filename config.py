import os
from dotenv import load_dotenv

load_dotenv("/home/evaristo/PycharmProjects/officina/mech_ai/.env")                     # carrega .env se existir

# ------------------- Gemini -------------------
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ------------------- Google Sheets -------------
# ID da planilha (extraído da URL: https://docs.google.com/spreadsheets/d/<<ID>>/edit)
SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")

# Nome da aba onde os registros serão inseridos
SHEETS_TAB_NAME = os.getenv("SHEETS_TAB_NAME", "Registros")
# Caminho para o arquivo de credenciais JSON baixado da console Google 

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite+aiosqlite:///mech_ai.db'