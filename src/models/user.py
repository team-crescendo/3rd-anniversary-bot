from typing import Optional

from sqlalchemy import BigInteger, Column, Integer
from sqlalchemy.orm import relationship

from . import Base
from .event import events


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    sticker = Column(Integer, default=0, nullable=False)

    rules = relationship("Rule", secondary=events, back_populates="users")


def get_user(session, user_id: int) -> Optional[User]:
    return session.query(User).filter(User.id == user_id).one_or_none()


def get_or_create_user(session, user_id: int) -> User:
    user = get_user(session, user_id)
    if user is not None:
        return user

    user = User(id=user_id)
    session.add(user)
    session.commit()
    return user


def add_sticker(session, user_id: int, amount: int):
    user = get_user(session, user_id)
    if user is None:
        session.add(User(id=user_id, sticker=amount))
    else:
        user.sticker += amount
