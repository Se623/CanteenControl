from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Dish(SqlAlchemyBase):
    __tablename__ = 'dishes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=True)
    image = Column(String, nullable=True)
    description = Column(String, nullable=True)
    timesbought = Column(Integer, nullable=True)

    requests = relationship("Request")
    ingridients_log = relationship("IngridientLog")
    ratings_log = relationship("RatingLog")