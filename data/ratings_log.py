from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class RatingLog(SqlAlchemyBase):
    __tablename__ = 'ratings_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    rate = Column(Float, nullable=True)

    dishes = relationship("Dish", back_populates="ratings_log")
    users = relationship("User", back_populates="ratings_log")


