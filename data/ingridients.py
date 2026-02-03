from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Ingridient(SqlAlchemyBase):
    __tablename__ = 'ingridients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)

    ingridients_log = relationship("IngridientLog")