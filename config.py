"""
config.py — Application configuration loaded from .env
All database credentials must remain in .env, never hardcoded here.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask secret key — read from .env
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-key-change-in-production")

    # MySQL connection — read from .env (DATABASE_URL)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Suppress FSA deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings for stability
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
