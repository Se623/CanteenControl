import os

from flask import Flask, redirect, render_template, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user 
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid, Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from datetime import datetime

from data import db_session
from data.dishes import Dish
from data.ingridients import Ingridient
from data.ingridients_log import IngridientLog
from data.ratings_log import RatingLog
from data.roles import Role
from data.requests import Request
from data.users import User
from forms.supply_request import SupplyForm
from forms.user import LoginForm, RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)

# Получить роль пользователя (внутри шаблона)
@app.template_filter('get_role')
def role_filter(user):
    db_sess = db_session.create_session()
    role = db_sess.get(Role, user.role).role
    return role

# Главная страница
@app.route('/')
def index():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        student = db_sess.get(User, current_user.id)
        if student.subscription_end != None and student.subscription_end < datetime.today():
            student.subscription_end = None
        db_sess.commit()
    return render_template("index.html")

# Добавить деньги на аккаунт
@app.route('/payment/money', methods=['POST'])
@login_required
def add_money():
    db_sess = db_session.create_session()
    money = request.form['money']
    student = db_sess.get(User, current_user.id)
    student.money += money
    db_sess.commit()
    return redirect("/")

# Добавить абонемент на аккаунт
@app.route('/payment/subscription', methods=['POST'])
@login_required
def add_months():
    db_sess = db_session.create_session()
    months = request.form['months']
    student = db_sess.get(User, current_user.id)
    if student.subscription_end == None or student.subscription_end < datetime.today():
        student.subscription_end = datetime.today() + datetime.timedelta(months * 30)
    else:
        student.subscription_end += datetime.timedelta(months * 30)
    db_sess.commit()
    return redirect("/")

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            surname=form.surname.data,
            name=form.name.data,
            patronymic=form.patronymic.data,
            email=form.email.data,
            role=db_sess.query(Role).filter(Role.role == "ученик").first().id,
            money=0
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

# Список блюд
@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    db_sess = db_session.create_session()
    dishes = db_sess.query(Dish).all()
    return render_template("menu.html", dishes=dishes)

# Создать заявку на пополнение еды
@app.route('/menu/supply', methods=['GET', 'POST'])
@login_required
def supply():
    form = SupplyForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        db_sess.add(Request(dish_id=form.dish.data.id, quantity=form.quantity.data, sender_id=current_user.id, isaccepted=0))
        db_sess.commit()
        return redirect("/")                                        

    return render_template('supply.html', form=form)


# Страница блюда
@app.route('/menu/dish/<int:dish_id>', methods=['GET', 'POST'])
@login_required
def dish(dish_id):
    db_sess = db_session.create_session()
    db_dish = db_sess.get(Dish, dish_id)
    
    ingridients = []
    ingridient_logs = db_sess.query(IngridientLog).filter(IngridientLog.dish_id == db_dish.id).all()
    for log in ingridient_logs:
        ingridients.append(db_sess.query(Ingridient).filter(Ingridient.id == log.ingridient_id).first().name) 

    return render_template("dish.html", dish=db_dish, ingridients=", ".join(ingridients))

# Оценить блюдо
@app.route('/menu/dish/<int:dish_id>/rate', methods=['POST'])
@login_required
def rate_dish(dish_id):
    db_sess = db_session.create_session()
    rate = request.form['rating']
    db_sess.add(RatingLog(dish_id=dish_id, student_id=current_user.id, rate=rate))
    db_sess.commit()
    return redirect("/menu/dish/<int:dish_id>")

# Купить блюдо
@app.route('/menu/dish/<int:dish_id>/buy', methods=['POST'])
@login_required
def buy_dish(dish_id):
    db_sess = db_session.create_session()
    quantity = request.form['quantity']
    db_sess.add(Request(dish_id=dish_id, quantity=quantity, sender_id=current_user.id))
    db_sess.commit()
    return redirect("/")


# Страница выдачи блюд
@app.route('/distribution', methods=['GET'])
@login_required
def distribution():
    db_sess = db_session.create_session()
    student_requests = db_sess.query(Request).filter(db_sess.get(Role, db_sess.get(User, Request.sender_id).role) == "ученик")
    return render_template("distribution.html", requests=student_requests)


# Выдать блюдо ученику
@app.route('/distribution/<int:request_id>/exec', methods=['POST'])
@login_required
def trigger_distribution(request_id):
    db_sess = db_session.create_session()
    student = db_sess.get(User, db_sess.get(Request, request_id).sender_id)
    student.money -= db_sess.get(Dish, db_sess.get(Request, request_id).dish_id).price * Dish, db_sess.get(Request, request_id).quantity
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    return redirect("/distribution")


# Удалить заявку на выдачу
@app.route('/distribution/<int:request_id>/del', methods=['POST'])
@login_required
def delete_distribution(request_id):
    db_sess = db_session.create_session()
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    return redirect("/distribution")


# Страница закупки блюд
@app.route('/procurement', methods=['GET'])
@login_required
def procurement():
    db_sess = db_session.create_session()
    cook_requests = db_sess.query(Request).join(User).join(Role).filter(Role.role == "повар").all()
    return render_template("procurement.html", requests=cook_requests)


# Закупить блюдо в столовую
@app.route('/procurement/<int:request_id>/exec', methods=['POST'])
@login_required
def trigger_procurement(request_id):
    db_sess = db_session.create_session()
    dish = db_sess.get(Dish, db_sess.get(Request, request_id).dish_id)
    dish.quantity += db_sess.get(Request, request_id).quantity
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    return redirect("/procurement")


# Удалить заявку на закупку
@app.route('/procurement/<int:request_id>/del', methods=['POST'])
@login_required
def delete_procurement(request_id):
    db_sess = db_session.create_session()
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    return redirect("/procurement")

# Страница статистики по оценке
@app.route('/statistics/rate', methods=['GET', 'POST'])
@login_required
def statistics_rate():
    data = {"dishes": [], "rate": []}
    db_sess = db_session.create_session()

    for dish in db_sess.query(Dish).all():
        data['dishes'].append(dish.name)
        logs = db_sess.query(RatingLog).filter(RatingLog.dish_id == dish.id).all()
        if len(logs) != 0:
            data['rate'].append(sum(logs, key=lambda x: x.rate) / len(logs))
        else:
            data['rate'].append(0)

    plot = figure(title="Блюда (Оценка)", 
                  x_range = FactorRange(factors=data["dishes"]),
                  y_range = Range1d(start=0,end=max(data["rate"])*1.5),
                  width=1200,
                  height=500, 
                  min_border=0, 
                  toolbar_location="above",
                  outline_line_color="#666666")

    glyph = VBar(x="dishes", top="rate", bottom=0, width=.8)
    plot.toolbar.logo = None
    plot.add_glyph(ColumnDataSource(data), glyph)

    script, div = components(plot)
    return render_template("statistics.html", script=script, div=div)

# Страница статистики по кол-ву покупок
@app.route('/statistics/times', methods=['GET', 'POST'])
@login_required
def statistics_times():
    data = {"dishes": [], "timesBought": []}
    db_sess = db_session.create_session()

    for dish in db_sess.query(Dish).all():
        data['dishes'].append(dish.name)
        data['timesBought'].append(dish.timesbought)

    plot = figure(title="Блюда (Кол-во заказов)", 
                  x_range = FactorRange(factors=data["dishes"]),
                  y_range = Range1d(start=0,end=max(data["timesBought"])*1.5),
                  width=1200,
                  height=500, 
                  min_border=0, 
                  toolbar_location="above",
                  outline_line_color="#666666")

    glyph = VBar(x="dishes", top="timesBought", bottom=0, width=.8)
    plot.toolbar.logo = None
    plot.add_glyph(ColumnDataSource(data), glyph)

    script, div = components(plot)
    return render_template("statistics.html", script=script, div=div)


# Создать отчёт
@app.route('/statistics/report', methods=['POST'])
@login_required
def statistics_report():
    db_sess = db_session.create_session()

    return redirect("/statistics/times")


# Выход из аккаунта
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    db_session.global_init("db/canteen_database.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)