import psycopg2
import psycopg2.extras
import psycopg2.errors


class UniqueViolationError(Exception):
    pass


def handle_unique_violation_error(conn, url_string):
    try:
        url_data = get_url_data(conn, ['id'], f"name='{url_string}'")
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
        cursor.execute('SELECT DISTINCT id, name FROM urls;')
        urls_data = cursor.fetchall()

        url_checks_data = []
        for url_data in urls_data:
            cursor.execute('''
                SELECT created_at, status_code
                FROM url_checks
                WHERE url_id = %s
                ORDER BY created_at DESC;
            ''', (url_data.id,))
            url_check_data = cursor.fetchone()
            if url_check_data:
                url_checks_data.append(url_check_data)

    urls = [
        {
            'id': url_data.id,
            'name': url_data.name,
            'created_at': url_check_data.created_at if url_check_data else None,
            'status_code': url_check_data.status_code if url_check_data else None,
        }
        for url_data, url_check_data in zip(urls_data, url_checks_data)
    ]

    return urls


def add_url(conn, url_string):
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


def get_url_data(conn, fields, condition, condition_params=None):
    if condition_params is None:
        condition_params = {}

    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        query = f"SELECT {', '.join(fields)} FROM urls WHERE {condition}"
        cursor.execute(query, condition_params)
        url_data = cursor.fetchone()
    return url_data


def get_url_checks(conn, url_id):
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute('SELECT * FROM url_checks WHERE url_id=%s', (url_id,))
        url_checks = cursor.fetchall()
    return url_checks


def insert_check_result(conn, url_id, code, h1, title, description):
    with conn.cursor() as cursor:
        cursor.execute("""INSERT INTO url_checks (
                            url_id,
                            status_code,
                            h1,
                            title,
                            description
                        ) values (
                            %(url_id)s,
                            %(status_code)s,
                            %(h1)s,
                            %(title)s,
                            %(description)s
                        )""",
                       {
                           'url_id': int(url_id),
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
