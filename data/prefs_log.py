from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class PreferenceLog(SqlAlchemyBase):
    __tablename__ = 'prefs_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    ingridient = Column(Integer, ForeignKey("ingridients.id"))
    is_liked = Column(Boolean, nullable=True)

    users = relationship("User", back_populates="prefs_log")
    ingridients = relationship("Ingridient", back_populates="prefs_log")