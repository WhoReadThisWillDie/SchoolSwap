from flask import Flask, render_template, redirect, make_response, request, session, abort
from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
@app.route('/index')
def index():
    pass


@app.route('registration', methods=['GET', 'POST'])
def register():
    pass


@app.route('login', methods=['GET', 'POST'])
def login():
    pass