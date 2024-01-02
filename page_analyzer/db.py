from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import psycopg2.errors
from datetime import datetime
from flask import flash


load_dotenv()


class UniqueViolationError(Exception):
    pass


def handle_unique_violation_error(conn, url_string):
    try:
        url_data = get_url(conn, f"name='{url_string}'")
        flash('Страница уже существует', 'info')
        return url_data
    finally:
        close_connection(conn)


def add_url_with_error_handling(conn, url_string):
    try:
        url_data = add_url(conn, url_string)
        close_connection(conn)
        return url_data
    except psycopg2.errors.UniqueViolation:
        raise UniqueViolationError


def get_db_connection(datebase_url):
    conn = psycopg2.connect(datebase_url)
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


def add_url(conn, url_string):
    if url_exists(conn, url_string):
        return get_url(conn, f"name='{url_string}'")

    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute("""
            INSERT INTO urls (name, created_at)
            values(%(url)s, CURRENT_TIMESTAMP)
            RETURNING id
        """, {
            'url': url_string,
        })
        url_id = cursor.fetchone()
        conn.commit()
    return url_id


def get_url(conn, condition, condition_params=None):
    if condition_params is None:
        condition_params = {}

    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        query = f"SELECT * FROM urls WHERE {condition}"
        cursor.execute(query, condition_params)
        url_data = cursor.fetchone()
    return url_data


def get_url_checks(conn, url_id):
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute(f'SELECT * FROM url_checks WHERE url_id={url_id}')
        url_checks = cursor.fetchall()
    return url_checks


def insert_check_result(conn, url_id, code, h1, title, description):
    with conn.cursor() as cursor:
        cursor.execute("""INSERT INTO url_checks (
                            url_id,
                            created_at,
                            status_code,
                            h1,
                            title,
                            description
                        ) values (
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
                       }
                       )
    conn.commit()


def url_exists(conn, url_string):
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM urls WHERE name = %s", (url_string,))
        return cursor.fetchone()[0] > 0
