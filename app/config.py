import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_hex(32)

class Config:
    # Generate secure SECRET_KEY if not provided
    SECRET_KEY = os.environ.get("SECRET_KEY") or generate_secret_key()
    
    # Default to sqlite for simplicity. To use Postgres, set DATABASE_URL env var.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "data.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", DEFAULT_UPLOAD_FOLDER)
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB upload limit
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Session security
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Remember me cookie security
    REMEMBER_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # Allowed file extensions for upload
    ALLOWED_EXTENSIONS = {
        # Documents
        'doc', 'docx', 'odt', 'txt', 'rtf',
        # PDFs
        'pdf',
        # Spreadsheets
        'xls', 'xlsx', 'ods', 'csv',
        # Archives
        'zip', 'rar', '7z'
    }
