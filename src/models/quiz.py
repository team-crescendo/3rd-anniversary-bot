from sqlalchemy import BigInteger, Boolean, Column, Integer, String
from sqlalchemy.sql.expression import func

from . import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    answer = Column(String(20), nullable=False, unique=True)
    image = Column(String(120), nullable=False)

    display = Column(Boolean, default=False, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    hint = Column(String)
    message_id = Column(BigInteger)


def select_random_quiz(session):
    quiz = session.query(Quiz).filter_by(used=False).order_by(func.random()).first()
    quiz.display = True
    quiz.used = True
    return quiz


def get_current_quiz(session):
    return session.query(Quiz).filter_by(display=True).one_or_none()
