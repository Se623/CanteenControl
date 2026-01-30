from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Role(SqlAlchemyBase):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String, nullable=True)

    users = relationship("User")