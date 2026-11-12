import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DEVELOPMENT_DB = os.getenv("DEVELOPEMENT_DB")

if not DEVELOPMENT_DB:
    raise RuntimeError("DEVELOPEMENT_DB must be defined in the .env file")

if DEVELOPMENT_DB == "sqlite":
    DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'data' / 'library.db').as_posix()}"
else:
    DATABASE_URL = DEVELOPMENT_DB
