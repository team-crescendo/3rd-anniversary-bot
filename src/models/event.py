from sqlalchemy import Column, ForeignKey, Table

from . import Base

events = Table(
    "events",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("rule_id", ForeignKey("rules.id"), primary_key=True),
)
