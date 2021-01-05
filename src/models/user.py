from typing import Optional

from sqlalchemy import BigInteger, Column, Integer

from . import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    sticker = Column(Integer, default=0, nullable=False)


def get_user(session, user_id: int) -> Optional[User]:
    return session.query(User).filter(User.id == user_id).one_or_none()


def add_sticker(session, user_id: int, amount: int):
    user = get_user(session, user_id)
    if user is None:
        session.add(User(id=user_id, sticker=amount))
    else:
        user.sticker += amount
