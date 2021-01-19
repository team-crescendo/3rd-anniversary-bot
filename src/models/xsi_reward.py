from typing import Optional
from sqlalchemy import Boolean, BigInteger, Column, Integer

from . import Base


class XsiReward(Base):
    __tablename__ = "xsi_rewards"

    id = Column(BigInteger, primary_key=True)
    sticker = Column(Integer, nullable=False)
    is_received = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<XsiReward id={self.id}, sticker={self.sticker}>"


def get_xsi_reward(session, discord_id: int) -> Optional[XsiReward]:
    return (
        session.query(XsiReward)
        .filter_by(id=discord_id, is_received=False)
        .one_or_none()
    )
