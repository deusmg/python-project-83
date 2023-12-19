import os
import psycopg2
import psycopg2.extras
import psycopg2.errors
from psycopg2.errorcodes import UNIQUE_VIOLATION
from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    flash,
    get_flashed_messages,
    make_response
)
import requests
from dotenv import load_dotenv
from page_analyzer import utils
from page_analyzer import db

app = Flask(__name__)
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
app.secret_key = "SECRET_KEY"


@app.route('/')
def home_page():
    return render_template('pages/home.html',)


@app.get('/urls')
def urls_list():
    conn = db.get_db_connection()
    urls = db.get_urls_list(conn)
    messages = get_flashed_messages(with_categories=True)

    return render_template(
        'pages/urls.html',
        messages=messages,
        urls_list=urls
    )


@app.post('/urls')
def add_urls():
    conn = db.get_db_connection()
    url = request.form.get('url')
    is_valid, error_txt = utils.url_validate(url)

    if not is_valid:
        flash(*error_txt, 'danger')
        return make_response(render_template('pages/home.html', url_name=url), 422)
    else:
        url_string = utils.prepare_url(url)

    try:
        url_data = db.add_url(conn, url_string)
        flash('Страница успешно добавлена', 'success')
    except psycopg2.errors.lookup(UNIQUE_VIOLATION):
        url_data = db.get_url_data(conn, ['id'], f"name='{url_string}'")
        flash('Страница уже существует', 'info')

    return redirect(url_for('url_profile', url_id=url_data.id), 302)


# страница профиля
@app.route('/urls/<int:url_id>')
def url_profile(url_id):
    conn = db.get_db_connection()
    messages = get_flashed_messages(with_categories=True)
    url_data = db.get_url_data(conn, ['*'], f"id={url_id}")
    url_checks = db.get_url_checks(conn, url_id)

    if not url_data:
        return handle_bad_request("404 id not found")

    return render_template(
        'pages/url_info.html',
        messages=messages,
        url_data=url_data,
        url_checks=url_checks
    )


@app.post('/urls/<int:url_id>/checks')
def url_checker(url_id):
    conn = db.get_db_connection()
    url_data = db.get_url_data(conn, ['name'], f"id={url_id}")

    try:
        r = requests.get(url_data.name)
        code = r.status_code

        if code >= 500:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('url_profile', url_id=url_id), 302)

        title, h1, description = utils.parse_html(r.text)

    except OSError:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_profile', url_id=url_id), 302)

    db.insert_check_result(conn, url_id, code, h1, title, description)
    flash('Страница успешно проверена', 'success')

    return redirect(url_for('url_profile', url_id=url_id), 302)


def handle_bad_request(e):
    return render_template('pages/404.html'), 404


app.register_error_handler(404, handle_bad_request)
