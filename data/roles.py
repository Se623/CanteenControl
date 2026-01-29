from sqlalchemy import Column, Integer, String
from .db_session import SqlAlchemyBase


class Role(SqlAlchemyBase):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String, nullable=True)