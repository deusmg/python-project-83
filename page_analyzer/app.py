from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool
from urllib.parse import urlparse
from validators.url import url
from datetime import datetime

app = Flask(__name__)

app.secret_key = "secret_key"

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def get_connection():
    return connection_pool.getconn()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_url', methods=['POST'])
def add_url():
    url_input = request.form['url']
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM urls WHERE name = %s", (url_input,))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("INSERT INTO urls (name, created_at) VALUES (%s, NOW())", (url_input,))
                conn.commit()
                flash('URL добавлен успешно', 'success')
            else:
                flash('URL уже существует', 'error')
    except psycopg2.Error as e:
        app.logger.error(f"Error executing SQL: {e}")
        flash('Произошла ошибка при выполнении запроса к базе данных', 'error')
    finally:
        conn.close()

    return redirect(url_for('index'))

@app.route('/urls')
def show_urls():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM urls")
            urls = cursor.fetchall()
    except psycopg2.Error as e:
        app.logger.error(f"Error executing SQL: {e}")
        flash('Произошла ошибка при выполнении запроса к базе данных', 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()

    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
            url_data = cursor.fetchone()

    if url_data:
        return render_template('url.html', url=url_data)
    else:
        return redirect(url_for('show_urls'))

if __name__ == '__main__':
    app.run(debug=True)
