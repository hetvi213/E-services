import os
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv()


def _database_uri():
    explicit_uri = os.getenv("SQLALCHEMY_DATABASE_URI")
    if explicit_uri:
        return explicit_uri

    user = quote_plus(os.getenv("MYSQL_USER", "root"))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    database = quote_plus(os.getenv("MYSQL_DATABASE", "gov_services"))
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
    PORTAL_ADDRESS = os.getenv("PORTAL_ADDRESS", "Krishi E-Government Services, Main Road, Ahmedabad, Gujarat")
    PORTAL_PHONE = os.getenv("PORTAL_PHONE", "+91 98765 43210")
    PORTAL_EMAIL = os.getenv("PORTAL_EMAIL", ADMIN_EMAIL)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    ADMIN_LOGIN_EMAIL = os.getenv("ADMIN_LOGIN_EMAIL", "")
    ADMIN_LOGIN_PASSWORD = os.getenv("ADMIN_LOGIN_PASSWORD", "")
