from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class IngridientLog(SqlAlchemyBase):
    __tablename__ = 'ingridients_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"))
    ingridient_id = Column(Integer, ForeignKey("ingridients.id"))

    dishes = relationship("Dish", back_populates="ingridients_log")
    ingridients = relationship("Ingridient", back_populates="ingridients_log")