import sqlalchemy
from .db_session import SqlAlchemyBase


class Dishes(SqlAlchemyBase):
    __tablename__ = 'dishes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    ingridients = sqlalchemy.Column(sqlalchemy.String, nullable=True)