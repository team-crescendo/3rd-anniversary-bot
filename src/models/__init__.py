import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('PSYCOPG2_CONNECTION')}", echo=True
)
Base = declarative_base()

Session = sessionmaker(bind=engine)
