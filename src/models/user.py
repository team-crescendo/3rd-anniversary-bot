from typing import Optional, Tuple

from sqlalchemy import Boolean, BigInteger, Column, Integer, String
from sqlalchemy.orm import relationship

from . import Base
from .event import events


STICKER_MAX = 20


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    sticker = Column(Integer, default=0, nullable=False)
    get_reward = Column(Boolean, default=False, nullable=False)
    formlink = Column(String)

    rules = relationship("Rule", secondary=events, back_populates="users")

    def __repr__(self) -> str:
        return f"<User {self.id}, sticker={self.sticker}>"

    def get_info(self) -> str:
        return f"{self.sticker}장 / {self.formlink}"


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


def add_sticker(session, user_id: int, amount: int) -> Tuple[int, int]:
    """(지급 이전 스티커, 지급 이후 스티커)를 튜플로 반환합니다."""
    user = get_user(session, user_id)
    if user is None:
        session.add(User(id=user_id, sticker=amount))
        return 0, amount
    else:
        before = user.sticker
        user.sticker = min(STICKER_MAX, user.sticker + amount)
        return before, user.sticker


def count_formlinks(session) -> int:
    return session.query(User).filter(User.formlink.isnot(None)).count()


def search_by_formlink(session, formlink: str) -> Optional[User]:
    return session.query(User).filter(User.formlink == formlink).one_or_none()
