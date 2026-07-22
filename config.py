import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///database.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")

    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")