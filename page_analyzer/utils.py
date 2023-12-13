from validators.url import url as url_validator
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def url_validate(url):
    is_valid = True
    error_txt = ""

    if url == "":
        error_txt = 'URL обязателен'
        is_valid = False
    elif len(url) > 255:
        error_txt = 'URL превышает 255 символов'
        is_valid = False
    elif url_validator(url) is not True:
        error_txt = 'Некорректный URL'
        is_valid = False

    return is_valid, error_txt


def prepare_url(url):
    u_s = urlparse(url)
    url_string = f'{u_s.scheme}://{u_s.hostname}'

    if u_s.port:
        url_string += f':{u_s.port}'

    return url_string


def parse_html(html_str):
    page_content = BeautifulSoup(html_str, features="html.parser")

    title = ''
    h1 = ''
    description = ''

    title_element = page_content.title
    if title_element:
        title = title_element.text

    h1_element = page_content.h1
    if h1_element:
        h1 = h1_element.text

    page_meta = page_content.findAll('meta')
    for el in page_meta:
        if el.get('name') == 'description':
            description = el.get('content')

    return title, h1, description
