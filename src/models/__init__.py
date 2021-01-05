from inspect import trace
import os
import traceback
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('PSYCOPG2_CONNECTION')}", echo=True
)
Base = declarative_base()

Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:  # noqa: E722
        session.rollback()
        traceback.print_exc()
        raise
    finally:
        session.close()
