import os

from flask import Flask, redirect, render_template
from flask_login import LoginManager, login_required, login_user, logout_user, current_user 
from sqlalchemy import update

from data import db_session
from data.dishes import Dish
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
    return render_template("index.html")

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

    if db_dish is None:
        return render_template('404.html'), 404

    return render_template("dish.html", dish=db_dish)


# Страница выдачи блюд
@app.route('/distribution', methods=['GET', 'POST'])
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
    db_sess.delete(student)
    db_sess.commit()
    student.money -= db_sess.get(Dish, db_sess.get(Request, request_id).dish_id).price * Dish, db_sess.get(Request, request_id).quantity
    db_sess.add(student)
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    return redirect("/distribution")


# Удалить заявку на выдачу
@app.route('/distribution/<int:request_id>/del', methods=['GET', 'POST'])
@login_required
def delete_distribution(request_id):
    db_sess = db_session.create_session()
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    return redirect("/distribution")


# Страница закупки блюд
@app.route('/procurement', methods=['GET', 'POST'])
@login_required
def procurement():
    db_sess = db_session.create_session()
    cook_requests = db_sess.query(Request).join(User).join(Role).filter(Role.role == "повар").all()
    return render_template("procurement.html", requests=cook_requests)


# Закупить блюдо в столовую
@app.route('/procurement/<int:request_id>/exec', methods=['GET', 'POST']) # TODO: Сделать POST функцию
@login_required
def trigger_procurement(request_id):
    db_sess = db_session.create_session()
    dish = db_sess.get(Dish, db_sess.get(Dish, request_id).dish_id)
    db_sess.delete(dish)
    db_sess.commit()
    dish.quantity += db_sess.get(Request, request_id).quantity
    db_sess.add(dish)
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