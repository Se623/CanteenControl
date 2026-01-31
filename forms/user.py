from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, SubmitField, EmailField
from wtforms.validators import InputRequired


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[InputRequired()])
    password = PasswordField('Пароль', validators=[InputRequired()])
    password_again = PasswordField('Повторите пароль', validators=[InputRequired()])
    surname = StringField('Фамилия пользователя', validators=[InputRequired()])
    name = StringField('Имя пользователя', validators=[InputRequired()])
    patronymic = StringField('Отчество пользователя')
    submit = SubmitField('Войти')

class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[InputRequired()])
    password = PasswordField('Пароль', validators=[InputRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')