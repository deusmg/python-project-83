from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
from validators.url import url

app = Flask(__name__)

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
        return render_template('index.html', error='Невалидный URL')

    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO urls (name) VALUES (%s)", (url_input,))
        conn.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
