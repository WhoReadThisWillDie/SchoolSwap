from flask import Flask, render_template, redirect, make_response, request, session, abort
from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    db_sess = db_session.create_session()
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            return render_template("register.html", title='Регистрация', form=form, message='Пароли не совпадают')
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title='Регистрация', form=form,
                                   message='Такой пользователь уже существует')
        user = User(
            username=form.username.data,
            classnum=form.classnum.data,
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
            return redirect('/')
        return render_template("login.html", form=form, title='Авторизация', message="Неправильный логин или пароль")
    return render_template('login.html', form=form, title='Авторизация')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


def main():
    db_session.global_init('db/SchoolSwap.sqlite')
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
