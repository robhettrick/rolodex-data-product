from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

# Only include 'check_same_thread' if using SQLite
connect_args = {}
url = make_url(DATABASE_URL)
if url.drivername.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()