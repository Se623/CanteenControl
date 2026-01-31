from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Dish(SqlAlchemyBase):
    __tablename__ = 'dishes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    rate = Column(Float, nullable=True)
    image = Column(String, nullable=True)

    supply_requests = relationship("SupplyRequest")