from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import InputRequired

from data import db_session
from data.dishes import Dish

def get_dishes():
    return db_session.create_session().query(Dish).all()

class SupplyForm(FlaskForm):
    dish = QuerySelectField('Блюдо', query_factory=get_dishes, get_label='name', validators=[InputRequired()])
    quantity = IntegerField('Количество', validators=[InputRequired()])
    submit = SubmitField('Отправить')
        