import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration. Values are read from environment variables so that
    no secrets ever live in source control."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # ---- Database -----------------------------------------------------
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "dsg_bank")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---- Sessions / security -------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    WTF_CSRF_TIME_LIMIT = None

    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCK_MINUTES = 15

    # ---- App-level constants --------------------------------------------
    MIN_TRANSFER_AMOUNT = 1
    MAX_DAILY_TRANSFER_LIMIT = 200000
    CURRENCY_SYMBOL = "\u20b9"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
