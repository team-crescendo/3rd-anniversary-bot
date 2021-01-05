from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Column, Integer, String

from . import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    by_admin = Column(Boolean, nullable=False)

    reward_sticker = Column(Integer, default=0, nullable=False)
    reward_role_id = Column(BigInteger)

    message_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    emoji = Column(String(50))

    def __repr__(self):
        if self.by_admin:
            description = f"관리자가 <#{self.channel_id}>에 {self.emoji} 추가"
        else:
            description = f"메시지 {self.message_id}에 {self.emoji} 추가"

        reward = f"{self.reward_sticker}장"
        if self.reward_role_id is not None:
            reward += f", <@&{self.reward_role_id}> 역할"

        return f"`#{self.id}` {self.name} - {description} ({reward})"


def list_all_rules(session) -> List[Rule]:
    return session.query(Rule).all()


def get_rule(session, rule_id: int) -> Optional[Rule]:
    return session.query(Rule).filter(Rule.id == rule_id).one_or_none()
