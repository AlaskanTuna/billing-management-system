# src/config.py

import os
import urllib.parse

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ENV

DOTENV =  Path(__file__).resolve().parent.parent / ".env"
load_dotenv(DOTENV)

# FILE SETTINGS

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static/"
TEMPLATES_DIR = ROOT / "templates/"

# APP CONFIGURATION

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

# DATABASE

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_TABLE_NAME = os.getenv("DB_TABLE_NAME")
CUSTOMERS_TABLE_NAME = "customers"

# SQLALCHEMY

SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)