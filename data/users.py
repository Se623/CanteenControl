from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    surname = Column(String, nullable=True)
    name = Column(String, nullable=True)
    patronymic = Column(String, nullable=True)
    email = Column(String, index=True, unique=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    role = Column(Integer, ForeignKey("roles.id"))
    money = Column(Float, nullable=True)
    subscription_end = Column(DateTime, nullable=True)

    roles = relationship("Role", back_populates="users")
    requests = relationship("Request")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)