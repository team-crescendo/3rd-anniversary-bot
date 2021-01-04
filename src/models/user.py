from sqlalchemy import BigInteger, Column, Integer

from . import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    sticker = Column(Integer)
