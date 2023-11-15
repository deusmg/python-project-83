from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
from validators.url import url as validate_url
from datetime import datetime

app = Flask(__name__)

app.secret_key = "secret_key"

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

def is_valid_url(url):
    return validate_url(url)

def url_exists(cursor, url):
    cursor.execute("SELECT COUNT(*) FROM urls WHERE name = %s", (url,))
    count = cursor.fetchone()[0]
    return count > 0

def insert_url(cursor, url):
    cursor.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s)", (url, datetime.today()))
    conn.commit()

def get_all_urls(cursor):
    cursor.execute("SELECT * FROM urls")
    return cursor.fetchall()

def get_url_by_id(cursor, url_id):
    cursor.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
    return cursor.fetchone()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_url', methods=['POST'])
def add_url():
    url_input = request.form.get('url')

    if not is_valid_url(url_input):
        flash('Невалидный URL', 'error')
        return redirect(url_for('index'))

    with conn.cursor() as cursor:
        if url_exists(cursor, url_input):
            flash('Этот URL уже существует', 'error')
        else:
            insert_url(cursor, url_input)
            flash('URL успешно добавлен', 'success')

    return redirect(url_for('index'))
    
@app.route('/urls')
def show_urls():
    with conn.cursor() as cursor:
        urls = get_all_urls(cursor)

    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with conn.cursor() as cursor:
        url_data = get_url_by_id(cursor, url_id)

    if url_data:
        return render_template('url.html', url=url_data)
    else:
        return redirect(url_for('show_urls'))

if __name__ == '__main__':
    app.run(debug=True)
