import os

from flask import Flask, abort, redirect, render_template, request, send_file
from flask_login import LoginManager, login_required, login_user, logout_user, current_user 
from werkzeug.exceptions import HTTPException
from bokeh.models import FactorRange, Range1d
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from datetime import datetime, timedelta

from data import db_session
from data.dishes import Dish
from data.ingridients import Ingridient
from data.ingridients_log import IngridientLog
from data.prefs_log import PreferenceLog
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

# Ошибка, когда нет денег
class PaymentRequired(HTTPException):
    code = 402
    header = 'Payment Required'
    description = 'The payment failed because there are insufficient funds in the target account.'

# Получить роль пользователя (внутри шаблона)
@app.template_filter('get_role')
def role_filter(user):
    db_sess = db_session.create_session()
    role = db_sess.get(Role, user.role).role
    return role

# Получить ФИО пользователя (внутри шаблона)
@app.template_filter('get_NSP')
def role_filter(request):
    db_sess = db_session.create_session()
    name = db_sess.get(User, request.sender_id).name
    surname = db_sess.get(User, request.sender_id).surname
    patronymic = db_sess.get(User, request.sender_id).patronymic
    return surname + " " + name + " " + patronymic

# Получить имя блюда (внутри шаблона)
@app.template_filter('get_dish')
def dish_filter(request): 
    db_sess = db_session.create_session()
    dish = db_sess.get(Dish, request.dish_id).name
    return dish

# Получить цену блюда (внутри шаблона)
@app.template_filter('get_price')
def price_filter(request):
    db_sess = db_session.create_session()
    price = db_sess.get(Dish, request.dish_id).price
    return price

# Получить ингридиент (внутри шаблона)
@app.template_filter('get_name')
def name_filter(log):
    db_sess = db_session.create_session()
    name = db_sess.get(Ingridient, log.ingridient).name
    return name

# Главная страница
@app.route('/')
def index():
    requests=None
    ingridients=None
    logs=None
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        student = db_sess.get(User, current_user.id)
        if student.subscription_end != None and student.subscription_end < datetime.today():
            student.subscription_end = None
        db_sess.commit()
        requests=db_sess.query(Request).filter(Request.sender_id == current_user.id).all()
        logs=db_sess.query(PreferenceLog).filter(PreferenceLog.student_id == current_user.id).all()
        ing_logs = [i.ingridient for i in logs]
        ings = []
        for i in ing_logs:
            ings.append(db_sess.get(Ingridient, i))
        ingridients=list(set(db_sess.query(Ingridient).all()) - set(ings))

    return render_template("index.html", requests=requests, ingridients=ingridients, logs=logs)

# Добавить предпочтение
@app.route('/prefs/add', methods=['POST'])
@login_required
def add_pre():
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "ученик":
        abort(403)
    ingridient = db_sess.query(Ingridient).filter(Ingridient.name == request.form['ingridients']).first().id
    is_liked = True if 'is_liked' in request.form else False

    db_sess.add(PreferenceLog(student_id=current_user.id, ingridient=ingridient, is_liked=is_liked))
    db_sess.commit()
    return redirect("/")


# Удалить предпочтение
@app.route('/prefs/<int:log_id>/del', methods=['POST'])
@login_required
def del_pref(log_id):
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "ученик":
        abort(403)
    db_sess.delete(db_sess.get(PreferenceLog, log_id))
    db_sess.commit()
    return redirect("/")

# Добавить деньги на аккаунт
@app.route('/payment/money', methods=['POST'])
@login_required
def add_money():
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "ученик":
        abort(403)
    money = int(request.form['money'])
    student = db_sess.get(User, current_user.id)
    student.money += money
    db_sess.commit()
    return redirect("/")

# Добавить абонемент на аккаунт
@app.route('/payment/subscription', methods=['POST'])
@login_required
def add_months():
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "ученик":
        abort(403)
    months = int(request.form['months'])
    student = db_sess.get(User, current_user.id)
    student.money -= months * 3000
    if student.subscription_end == None or student.subscription_end < datetime.today():
        student.subscription_end = datetime.today() + timedelta(months * 30)
    else:
        student.subscription_end += timedelta(months * 30)
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
@app.route('/menu', methods=['GET'])
@login_required
def menu():
    db_sess = db_session.create_session()
    dishes = db_sess.query(Dish).all()
    return render_template("menu.html", dishes=dishes)

# Создать заявку на пополнение еды
@app.route('/menu/supply', methods=['GET', 'POST'])
@login_required
def supply():
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "повар":
        abort(403)
    form = SupplyForm()
    if form.validate_on_submit():
        db_sess.add(Request(dish_id=form.dish.data.id, quantity=form.quantity.data, sender_id=current_user.id, is_accepted=False))
        db_sess.commit()
        return redirect("/")                                        

    return render_template('supply.html', form=form)


# Страница блюда
@app.route('/menu/dish/<int:dish_id>', methods=['GET'])
@login_required
def dish(dish_id):
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "ученик":
        abort(403)
    db_dish = db_sess.get(Dish, dish_id)
    
    ingridients = []
    ingridient_logs = db_sess.query(IngridientLog).filter(IngridientLog.dish_id == db_dish.id).all()
    for log in ingridient_logs:
        ingridients.append(db_sess.query(Ingridient).filter(Ingridient.id == log.ingridient_id).first().name) 

    prefs = db_sess.query(PreferenceLog).filter(PreferenceLog.student_id == current_user.id).filter(PreferenceLog.is_liked == True).all()
    prefs = [db_sess.get(Ingridient, x.ingridient).name for x in prefs]
    prefs = list(set(prefs) & set(ingridients))
    alers = db_sess.query(PreferenceLog).filter(PreferenceLog.student_id == current_user.id).filter(PreferenceLog.is_liked == False).all()
    alers = [db_sess.get(Ingridient, x.ingridient).name for x in alers]
    alers = list(set(alers) & set(ingridients))
    ratearr = db_sess.query(RatingLog).filter(RatingLog.dish_id == dish_id).all()
    userRate = db_sess.query(RatingLog).filter(RatingLog.dish_id == dish_id).filter(RatingLog.student_id == current_user.id).first()
    if userRate != None:
        userRate = userRate.rate

    if ratearr == []:
        rate = 0
    else:
        rate = sum([x.rate for x in ratearr]) / len(ratearr)
    return render_template("dish.html", dish=db_dish, ingridients=", ".join(ingridients), prefs=", ".join(prefs), alers=", ".join(alers), rate = rate, userRate=userRate)

# Оценить блюдо
@app.route('/menu/dish/<int:dish_id>/rate', methods=['POST'])
@login_required
def rate_dish(dish_id):
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "ученик":
        abort(403)
    rate = request.form['rating']
    userRate = db_sess.query(RatingLog).filter(RatingLog.dish_id == dish_id).filter(RatingLog.student_id == current_user.id).first()
    if userRate != None:
        db_sess.delete(userRate)
        db_sess.commit()
    db_sess.add(RatingLog(dish_id=dish_id, student_id=current_user.id, rate=rate))
    db_sess.commit()
    return redirect(f"/menu/dish/{dish_id}")

# Купить блюдо
@app.route('/menu/dish/<int:dish_id>/buy', methods=['POST'])
@login_required
def buy_dish(dish_id):
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "ученик":
        abort(403)
    quantity = request.form['quantity']
    db_sess.add(Request(dish_id=dish_id, quantity=quantity, sender_id=current_user.id, is_accepted=False))
    db_sess.commit()
    return redirect("/")


# Страница выдачи блюд
@app.route('/distribution', methods=['GET'])
@login_required
def distribution():
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "повар":
        abort(403)
    student_requests = db_sess.query(Request).join(User).join(Role).filter(Role.role == "ученик").filter(Request.is_accepted == False).all()
    return render_template("distribution.html", requests=student_requests)


# Выдать блюдо ученику
@app.route('/distribution/<int:request_id>/exec', methods=['POST'])
@login_required
def trigger_distribution(request_id):
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "повар":
        abort(403)
    if db_sess.get(Dish, db_sess.get(Request, request_id).dish_id).quantity < db_sess.get(Request, request_id).quantity:
        abort(403)
    student = db_sess.get(User, db_sess.get(Request, request_id).sender_id)
    dish = db_sess.get(Dish, db_sess.get(Request, request_id).dish_id)
    if student.subscription_end != None and student.subscription_end > datetime.today():
        pass
    elif student.money >= db_sess.get(Dish, db_sess.get(Request, request_id).dish_id).price * db_sess.get(Request, request_id).quantity:
        student.money -= db_sess.get(Dish, db_sess.get(Request, request_id).dish_id).price * db_sess.get(Request, request_id).quantity
        dish.quantity -= db_sess.get(Request, request_id).quantity
        db_sess.commit()
    else:
        raise PaymentRequired()
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    return redirect("/distribution")

# Удалить заявку на выдачу
@app.route('/distribution/<int:request_id>/del', methods=['POST'])
@login_required
def delete_distribution(request_id):
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role == "администратор":
        abort(403)
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    if db_sess.get(Role, current_user.id).role == "ученик":
        return redirect("/")
    else:
        return redirect("/distribution")


# Страница закупки блюд
@app.route('/procurement', methods=['GET'])
@login_required
def procurement():
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "администратор":
        abort(403)
    cook_requests = db_sess.query(Request).join(User).join(Role).filter(Role.role == "повар").all()
    return render_template("procurement.html", requests=cook_requests)


# Закупить блюдо в столовую
@app.route('/procurement/<int:request_id>/exec', methods=['POST'])
@login_required
def trigger_procurement(request_id):
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "администратор":
        abort(403)
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
    if db_sess.get(Role, current_user.id).role == "ученик":
        abort(403)
    db_sess.delete(db_sess.get(Request, request_id))
    db_sess.commit()
    if db_sess.get(Role, current_user.id).role == "повар":
        return redirect("/")
    else:
        return redirect("/procurement")

# Страница статистики по оценке
@app.route('/statistics/rate', methods=['GET', 'POST'])
@login_required
def statistics_rate():
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "администратор":
        abort(403)

    data = {"dishes": [], "timesBought": []}
    
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
    db_sess = db_session.create_session()
    if db_sess.get(Role, current_user.id).role != "администратор":
        abort(403)

    data = {"dishes": [], "timesBought": []}

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
@app.route('/statistics/export', methods=['POST'])
@login_required
def statistics_report():
    db_sess = db_session.create_session()
    if os.path.isfile("report.txt"):
        os.remove("report.txt")
    if db_sess.get(Role, current_user.id).role != "администратор":
        abort(403)
    revenue = 0
    student_logs = db_sess.query(Request).join(User).join(Role).filter(Role.role == "ученик").filter(Request.is_accepted == True).all()
    cook_logs = db_sess.query(Request).join(User).join(Role).filter(Role.role == "повар").filter(Request.is_accepted == True).all()

    for log in student_logs:
        revenue += log.quantity * db_sess.get(Dish, log.dish_id).price

    report_file=open('report.txt', 'w')
    report_file.write("Выручка столовой: " + str(revenue) + " рублей\n")
    report_file.write("Заказы учеников:\n")
    report_file.write("id;dish;quantity;sender_name;sender_surname;sender_patronymic;sender_email\n")
    for log in student_logs:
        report_file.write(str(log.id) + ";" + 
                          db_sess.get(Dish, log.dish_id).name + ";" +
                          str(log.quantity) + ";" +
                          db_sess.get(User, log.sender_id).name + ";" +
                          db_sess.get(User, log.sender_id).surname + ";" +
                          db_sess.get(User, log.sender_id).patronymic + ";" +
                          db_sess.get(User, log.sender_id).email + "\n")
    report_file.write("Заявки поваров:\n")
    for log in cook_logs:
        report_file.write(str(log.id) + ";" + 
                          db_sess.get(Dish, log.dish_id).name + ";" +
                          str(log.quantity) + ";" +
                          db_sess.get(User, log.sender_id).name + ";" +
                          db_sess.get(User, log.sender_id).surname + ";" +
                          db_sess.get(User, log.sender_id).patronymic + ";" +
                          db_sess.get(User, log.sender_id).email + "\n")
    report_file.close()
    return send_file("report.txt", as_attachment=True)


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