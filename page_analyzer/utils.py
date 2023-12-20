from validators.url import url as url_validator
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def url_validate(url):
    errors = []

    if url == "":
        errors.append('URL обязателен')
    elif len(url) > 255:
        errors.append('URL превышает 255 символов')
    elif url_validator(url) is not True:
        errors.append('Некорректный URL')

    return not errors, errors


def prepare_url(input_url):
    url = urlparse(input_url)
    url_string = f'{url.scheme}://{url.hostname}'
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
