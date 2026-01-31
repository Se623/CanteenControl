from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField
from wtforms.validators import InputRequired

from data import db_session
from data.dishes import Dish


class SupplyForm(FlaskForm):
    dish = SelectField('Блюдо', choices=[(x.name, x.name) for x in db_session.create_session().query(Dish).all()], validators=[InputRequired()])
    quantity = DecimalField('Количество', validators=[InputRequired()])
    submit = SubmitField('Отправить')