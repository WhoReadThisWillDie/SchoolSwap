import os
import sys
import requests
from flask import Flask, render_template, redirect, make_response, request, session, abort
from data import db_session
from data.users import User
from data.goods import Goods
from forms.goods import GoodsForm
from forms.users import RegisterForm, LoginForm, EditForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, send

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
UPLOAD_PATH = 'static/images/'


def get_map_picture():
    map_request = "https://static-maps.yandex.ru/1.x/?ll=37.596056,55.635236&z=15&l=map&pt=37.596056,55.635236,pm2rdm"
    response = requests.get(map_request)
    if not response:
        print("Ошибка выполнения запроса:")
        print(map_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    map_file = "static/img/map.png"
    with open(map_file, "wb") as file:
        file.write(response.content)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    goods = db_sess.query(Goods)
    if current_user.is_authenticated:
        return render_template("index.html", goods=goods)
    return render_template("hello.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    form = RegisterForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            return render_template("register.html", title='Регистрация', form=form, message='Пароли не совпадают')
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title='Регистрация', form=form,
                                   message='Такой пользователь уже существует')
        if db_sess.query(User).filter(User.phone == form.phone.data).first():
            return render_template("register.html", title='Регистрация', form=form,
                                   message='Такой пользователь уже существует')
        user = User(
            username=form.username.data,
            classnum=form.classnum.data,
            phone=form.phone.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template("register.html", title='Регистрация', form=form, message=message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/my_profile')
        return render_template("login.html", form=form, title='Авторизация', message="Неправильный логин или пароль")
    return render_template('login.html', form=form, title='Авторизация')


@app.route('/my_profile')
@login_required
def profile():
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.id == current_user.id).first()
    return render_template("my_profile.html", title="Профиль", users=users)


@app.route('/users/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    form = EditForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == id).first()
        if users:
            form.username.data = users.username
            form.classnum.data = users.classnum
            form.phone.data = users.phone
            form.email.data = users.email
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == id).first()
        if users:
            users.username = form.username.data
            users.classnum = form.classnum.data
            users.phone = form.phone.data
            users.email = form.email.data
            db_sess.commit()
            return redirect('/my_profile')
        else:
            abort(404)
    return render_template('edit_profile.html',
                           title='Редактирование профиля',
                           form=form)


@app.route('/users_delete/<int:id>', methods=['GET', 'POST'])
def delete_profile(id):
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.id == id).first()
    if users:
        db_sess.delete(users)
        db_sess.commit()
        redirect('/logout')
    else:
        abort(404)
    return redirect('/')


# @app.route('/profile/<int:id>')
# @login_required
# def seller_profile(id):
#     db_sess = db_session.create_session()
#     users = db_sess.query(User).filter(User.id == id).first()
#     return render_template('profile.html', title='Профиль продавцв', users=users)


@app.route('/my_goods', methods=['GET', 'POST'])
@login_required
def my_goods():
    db_sess = db_session.create_session()
    goods = db_sess.query(Goods).filter(Goods.user_id == current_user.id)
    if goods:
        return render_template("my_goods.html", goods=goods, title="Мои объявления")
    return redirect("/")


@app.route('/all_goods', methods=['GET', 'POST'])
@login_required
def all_goods():
    db_sess = db_session.create_session()
    goods = db_sess.query(Goods)
    if goods:
        return render_template("all_goods.html", goods=goods, title="Все объявления")
    return redirect("/my_profile")


@app.route('/add_goods', methods=['GET', 'POST'])
@login_required
def add_goods():
    form = GoodsForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        db_sess = db_session.create_session()
        goods = Goods()
        goods.title = form.title.data
        goods.description = form.description.data
        goods.price = form.price.data
        goods.picture = f"img/{filename}"
        current_user.goods.append(goods)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/my_goods')
    return render_template('add_goods.html', title='Добавление товара',
                           form=form)


@app.route('/goods/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_goods(id):
    form = GoodsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        goods = db_sess.query(Goods).filter(Goods.id == id, Goods.user == current_user).first()
        if goods:
            form.title.data = goods.title
            form.description.data = goods.description
            form.price.data = goods.price
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        goods = db_sess.query(Goods).filter(Goods.id == id, Goods.user == current_user).first()
        if goods:
            filename = secure_filename(form.file.data.filename)
            goods.title = form.title.data
            goods.description = form.description.data
            goods.price = form.price.data
            goods.picture = f"img/{filename}"
            db_sess.commit()
            return redirect('/my_goods')
        else:
            abort(404)
    return render_template('edit_goods.html',
                           title='Редактирование товара',
                           form=form)


@app.route('/goods_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def goods_delete(id):
    db_sess = db_session.create_session()
    goods = db_sess.query(Goods).filter(Goods.id == id,  Goods.user == current_user).first()
    if goods:
        db_sess.delete(goods)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/my_goods')


@app.route('/goods_info/<int:id>', methods=['GET', 'POST'])
def goods_info(id):
    db_sess = db_session.create_session()
    goods = db_sess.query(Goods).filter(Goods.id == id).first()
    return render_template('good.html',
                           goods=goods,
                           title='Товар')


@app.route('/profile/<int:id>', methods=['GET', 'POST'])
def profile_info(id):
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.id == id).first()
    return render_template('profile.html', users=users, title='Профиль продавца')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/about')
def about():
    return render_template('about.html', title='Подробнее')


def main():
    db_session.global_init('db/SchoolSwap.sqlite')
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    get_map_picture()
    main()
    os.remove('static/img/map.png')
