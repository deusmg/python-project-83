import os
from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    flash,
    get_flashed_messages,
    abort,
)
import requests
from dotenv import load_dotenv
from page_analyzer import utils
from page_analyzer import db

app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


@app.route('/')
def index():
    return render_template('pages/index.html',)


@app.get('/urls')
def get_urls():
    conn = db.get_db_connection(DATABASE_URL)
    urls = db.get_urls_list(conn)
    db.close_connection(conn)
    messages = get_flashed_messages(with_categories=True)

    return render_template(
        'pages/urls.html',
        messages=messages,
        urls_list=urls
    )


@app.post('/urls')
def add_urls():
    conn = db.get_db_connection(DATABASE_URL)
    url = request.form.get('url')
    url_errors = utils.url_validate(url)

    if url_errors:
        flash(*url_errors, 'danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template('pages/index.html', url_name=url, messages=messages), 422

    prepared_url = utils.prepare_url(url)

    try:
        url_info = db.get_url_info(conn, 'id', 'name=%(prepared_url)s', {'prepared_url': prepared_url})
        if url_info:
            flash('Страница уже существует', 'info')
        else:
            if db.url_exists(conn, prepared_url):
                return db.get_url_info(conn, 'id', 'name=%(prepared_url)s', {'prepared_url': prepared_url})
            else:
                url_info = db.add_url_with_error_handling(conn, prepared_url)
                flash('Страница успешно добавлена', 'success')
        db.close_connection(conn)
    except db.UniqueViolationError:
        url_info = db.handle_unique_violation_error(conn, prepared_url)
        flash('Страница уже существует', 'info')
        db.close_connection(conn)

    return redirect(url_for('get_url', url_id=url_info.id), 302)


@app.route('/urls/<int:url_id>')
def get_url(url_id):
    conn = db.get_db_connection(DATABASE_URL)
    messages = get_flashed_messages(with_categories=True)
    url_info = db.get_url_info(conn, '*', 'id=%(url_id)s', {'url_id': url_id})
    url_checks = db.get_url_checks(conn, url_id)
    db.close_connection(conn)
    if not url_info:
        abort(404)

    return render_template(
        'pages/url_info.html',
        messages=messages,
        url_info=url_info,
        url_checks=url_checks
    )


@app.post('/urls/<int:url_id>/checks')
def post_url_check(url_id):
    conn = db.get_db_connection(DATABASE_URL)
    url_info = db.get_url_info(conn, 'name', 'id=%(url_id)s', {'url_id': url_id})
    try:
        r = requests.get(url_info.name)
        code = r.status_code

        if code >= 500:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('get_url', url_id=url_id), 302)

        check_data = utils.parse_html(r.text)

    except OSError:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('get_url', url_id=url_id), 302)

    db.insert_url_check(conn, url_id, code, **check_data)
    db.close_connection(conn)
    flash('Страница успешно проверена', 'success')

    return redirect(url_for('get_url', url_id=url_id), 302)


@app.errorhandler(404)
def handle_bad_request(e):
    return render_template('pages/404.html'), 404


@app.errorhandler(500)
def handle_internal_server_error(e):
    return render_template('pages/500.html'), 500
