from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
from validators.url import url

app = Flask(__name__)

app.secret_key = "secret_key"

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_url', methods=['POST'])
def add_url():
    url_input = request.form.get('url')
    
    if not url(url_input):
        flash('Невалидный URL', 'error')
    else:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM urls WHERE name = %s", (url_input,))
            count = cursor.fetchone()[0]
            if count > 0:
                flash('Этот URL уже существует', 'error')
            else:
                cursor.execute("INSERT INTO urls (name) VALUES (%s)", (url_input,))
                conn.commit()
                flash('URL успешно добавлен', 'success')

    return redirect(url_for('index'))

@app.route('/urls')
def show_urls():
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM urls")
        urls = cursor.fetchall()

    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
        url_data = cursor.fetchone()

    if url_data:
        return render_template('url.html', url=url_data)
    else:
        return redirect(url_for('show_urls'))

if __name__ == '__main__':
    app.run(debug=True)
