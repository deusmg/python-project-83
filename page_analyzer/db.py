import psycopg2
import psycopg2.extras
import psycopg2.errors


class UniqueViolationError(Exception):
    pass


def handle_unique_violation_error(conn, url_string):
    try:
        url_info = get_url_info_by_id(conn, url_string)
        return url_info
    finally:
        close_connection(conn)


def add_url_with_error_handling(conn, url_string):
    try:
        url_info = add_url(conn, url_string)
        close_connection(conn)
        return url_info
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
        cursor.execute('SELECT id, name FROM urls;')
        urls_data = {url.id: url for url in cursor.fetchall()}

        cursor.execute('''
            SELECT url_id, MAX(created_at) AS created_at, MAX(status_code) AS status_code
            FROM url_checks
            GROUP BY url_id;
        ''')
        url_checks_data = {check.url_id: check for check in cursor.fetchall()}

    urls = [
        {
            'id': url_id,
            'name': url_data.name,
            'created_at': url_checks_data[url_id].created_at if url_id in url_checks_data else None,
            'status_code': url_checks_data[url_id].status_code if url_id in url_checks_data else None,
        }
        for url_id, url_data in urls_data.items()
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


def get_url_info_by_id(conn, name):
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute('SELECT id FROM urls WHERE name=%s', (name,))
        url_info = cursor.fetchone()
    return url_info


def get_url_info_by_name(conn, url_id):
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute('SELECT name FROM urls WHERE id=%s', (url_id,))
        url_info = cursor.fetchone()
    return url_info


def get_url_info_by_all(conn, url_id):
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute('SELECT * FROM urls WHERE id=%s', (url_id,))
        url_checks = cursor.fetchone()
    return url_checks


def get_url_checks(conn, url_id):
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute('SELECT * FROM url_checks WHERE url_id=%s', (url_id,))
        url_checks = cursor.fetchall()
    return url_checks


def insert_url_check(conn, url_id, code, h1, title, description):
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
