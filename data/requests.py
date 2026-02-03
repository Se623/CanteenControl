from sqlalchemy import Column, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Request(SqlAlchemyBase):
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"))
    quantity = Column(Integer, nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"))

    dishes = relationship("Dish", back_populates="requests")
    users = relationship("User", back_populates="requests")
    