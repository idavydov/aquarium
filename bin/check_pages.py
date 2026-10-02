#!/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'public'


class PageInfo(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.title = ''
        self.canonical = None
        self.links = []
        self.in_title = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href')
        if tag == 'a' and attrs.get('href', '').startswith('/'):
            self.links.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def fetch(base_url, path):
    request = Request(base_url.rstrip('/') + path,
                      headers={'User-Agent': 'aquarium-pages-check/1.0'})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise ValueError('HTTP %s' % response.status)
        return response.headers.get_content_type(), response.read()


def main():
    parser = argparse.ArgumentParser(description='Check local output or a Pages deployment.')
    parser.add_argument('base_url', nargs='?', help='For example https://aquarium.pages.dev')
    args = parser.parse_args()
    if args.base_url:
        parsed = urlsplit(args.base_url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path not in ('', '/'):
            parser.error('base_url must be an HTTP(S) site root')

    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    urls = [node.text for node in ET.parse(PUBLIC / 'sitemap.xml').findall(
        namespace + 'url/' + namespace + 'loc')]
    sources = list((ROOT / 'content' / 'аккорды').glob('*.html'))
    assert len(urls) == len(set(urls)) == len(sources) + 1, 'Wrong sitemap URL count'
    pages = []
    for url in urls:
        path = urlsplit(url).path
        filename = PUBLIC / (unquote(path).lstrip('/') + '.html' if path != '/' else 'index.html')
        info = PageInfo(filename.read_text(encoding='utf8'))
        assert info.title, 'Missing title: ' + path
        assert info.canonical == unquote(url), 'Wrong canonical: ' + path
        pages.append((path, info))

    index = PageInfo((PUBLIC / 'index.html').read_text(encoding='utf8'))
    expected_links = {unquote(path) for path, _ in pages if path != '/'}
    assert set(index.links) == expected_links, 'Index links differ from sitemap'
    assert (PUBLIC / '404.html').is_file(), 'Missing 404.html'
    assert (PUBLIC / 'robots.txt').read_bytes() == (ROOT / 'static' / 'robots.txt').read_bytes()
    print('Local output: %d pages, index links, canonicals, robots.txt and 404 checked' % len(pages))
    if not args.base_url:
        return

    def check_page(page):
        path, expected = page
        try:
            content_type, body = fetch(args.base_url, path)
            actual = PageInfo(body.decode('utf8'))
            if content_type != 'text/html' or (actual.title, actual.canonical) != (expected.title, expected.canonical):
                raise ValueError('Unexpected content type, title or canonical (possible homepage fallback)')
        except Exception as error:
            return '%s: %s' % (path, error)

    with ThreadPoolExecutor(max_workers=8) as executor:
        errors = [error for error in executor.map(check_page, pages) if error]
    for path in ('/robots.txt', '/sitemap.xml', '/css/bootstrap.min.css', '/favicon.ico'):
        try:
            _, body = fetch(args.base_url, path)
            if body != (PUBLIC / path.lstrip('/')).read_bytes():
                raise ValueError('Content differs from local build')
        except Exception as error:
            errors.append('%s: %s' % (path, error))
    try:
        fetch(args.base_url, '/__aquarium_missing_page_check__')
        errors.append('Missing page returned 200 instead of 404')
    except HTTPError as error:
        if error.code != 404:
            errors.append('Missing page returned HTTP %s' % error.code)
    except Exception as error:
        errors.append('Missing page check: %s' % error)
    if errors:
        parser.exit(1, '\n'.join(errors) + '\n')
    print('Deployment: all %d sitemap URLs, static assets and 404 checked' % len(pages))


if __name__ == '__main__':
    main()
