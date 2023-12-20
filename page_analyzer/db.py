import os
from datetime import datetime
import psycopg2
import psycopg2.extras
from psycopg2.errorcodes import UNIQUE_VIOLATION

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


class UniqueViolationError(Exception):
    pass


def get_db_connection(database_url):
    conn = psycopg2.connect(database_url)
    return conn


def close_connection(conn):
    conn.close()


def get_urls_list(conn):
    with conn.cursor(
        cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute('''
            SELECT DISTINCT ON (urls.id)
            urls.id,
            urls.name,
            url_checks.created_at,
            url_checks.status_code
            FROM urls
            LEFT JOIN url_checks ON urls.id = url_checks.url_id
            ORDER BY urls.id, url_checks.created_at DESC;
        ''')
        urls = cursor.fetchall()
    return urls


def add_url(database_url, url_string):
    conn = get_db_connection(database_url)
    try:
        with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        ) as cursor:
            cursor.execute("""
                INSERT INTO urls (name, created_at)
                VALUES (%(url)s, CURRENT_TIMESTAMP)
                RETURNING id
            """,
            {
                'url': url_string,
            })
            url_id = cursor.fetchone().id
            conn.commit()
        return url_id
    except psycopg2.errors.UniqueViolation:
        raise UniqueViolationError
    finally:
        close_connection(conn)


def get_url_data(database_url, fields, condition, condition_params=None):
    if condition_params is None:
        condition_params = {}

    conn = get_db_connection(database_url)
    try:
        with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        ) as cursor:
            query = f"SELECT {', '.join(fields)} FROM urls WHERE {condition}"
            cursor.execute(query, condition_params)
            url_data = cursor.fetchone()
        return url_data
    finally:
        close_connection(conn)


def get_url_checks(database_url, url_id):
    conn = get_db_connection(database_url)
    try:
        with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        ) as cursor:
            cursor.execute(f'SELECT * FROM url_checks WHERE url_id={url_id}')
            url_checks = cursor.fetchall()
        return url_checks
    finally:
        close_connection(conn)


def insert_check_result(database_url, url_id, code, h1, title, description):
    conn = get_db_connection(database_url)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""INSERT INTO url_checks (
                url_id,
                created_at,
                status_code,
                h1,
                title,
                description
            ) VALUES (
                %(url_id)s,
                %(date_time)s,
                %(status_code)s,
                %(h1)s,
                %(title)s,
                %(description)s
            )""",
            {
                'url_id': int(url_id),
                'date_time': datetime.today(),
                'status_code': int(code),
                'h1': h1,
                'title': title,
                'description': description
            })
        conn.commit()
    finally:
        close_connection(conn)
