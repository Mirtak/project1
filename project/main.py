from flask import Flask, request
from data import db_session
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired
from data.users import User
from flask import render_template, redirect
from forms.user import RegisterForm, FindForm
import webbrowser
from flask_login import LoginManager, login_user,  login_required, logout_user, current_user
import requests
from books_api import gbooks


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
org_api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
api_server = "http://static-maps.yandex.ru/1.x/"

login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/')
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if current_user.is_authenticated:
        return redirect('/find')
    if request.method == 'POST':
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть, авторизируйтесь")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=False)
        return redirect('/find')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/find', methods=['POST', 'GET'])
def find():
    form = FindForm()
    if request.method == 'GET':
        return render_template("form.html", title="Find a book", form=form)
    if form.validate_on_submit():
        book = request.form["book"]
        place = request.form["place"]
        toponym_to_find = place
        bk = gbooks()
        text = bk.search(book)
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

        geocoder_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": toponym_to_find,
            "format": "json"}

        response = requests.get(geocoder_api_server, params=geocoder_params)

        if not response:
            pass

        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

        delta = "0.00525"

        map_params = {
            "apikey": org_api_key,
            "text": "book+shops",
            "lang": "ru_RU",
            "ll": toponym_longitude + "," + toponym_lattitude,
            "spn": "0.552069,0.400552",
            "results": "50"
        }

        map_api_server = "https://search-maps.yandex.ru/v1/"
        response = requests.get(map_api_server, params=map_params)
        adresses = []
        response = response.json()
        for item in response["features"]:
            new_item = item["geometry"]["coordinates"]
            for j in range(len(new_item)):
                new_item[j] = str(new_item[j])
            new_item = ",".join(new_item)
            adresses.append(new_item)
        for i in range(len(adresses)):
            adresses[i] = adresses[i] + ",pm2lbm"

        show_place = ",".join([toponym_longitude, toponym_lattitude, "pm2rdm"])
        params = {
            "ll": ",".join([toponym_longitude, toponym_lattitude]),
            "spn": ",".join([delta, delta]),
            "l": "map",
            "size": "400,400",
            "pt": "~".join(adresses + [show_place])
        }
        response = requests.get(api_server, params=params)
        image = response.url
        return render_template("show.html", title="Find a book",
                               im=image, name_book=book, text=text)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/find")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/register")


def main():
    db_session.global_init("db/users.db")
    webbrowser.open('http://127.0.0.1:800/', new=2)
    app.run(port=800, host='127.0.0.1')


if __name__ == '__main__':
    main()