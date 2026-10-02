#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import print_function

import argparse
import glob
import os
import posixpath
import sys

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

try:
    unicode
except NameError:
    unicode = str

from xml.sax.saxutils import escape


DEFAULT_BASE_URL = 'https://aquarium.rifma.ch/'
DEFAULT_CONTENT_DIR = 'content'
DEFAULT_OUTPUT = 'public/sitemap.xml'


def to_text(value):
    if isinstance(value, unicode):
        return value
    return value.decode('utf8')


def urljoin(base_url, path):
    quoted_path = quote(to_text(path).lstrip('/').encode('utf8'), safe='/:')
    return to_text(base_url).rstrip('/') + '/' + to_text(quoted_path)


def source_paths(content_dir):
    yield ''

    pattern = os.path.join(content_dir, 'аккорды', '*.html')
    for filename in sorted(glob.glob(pattern)):
        relpath = os.path.relpath(filename, content_dir)
        relpath = relpath.replace(os.sep, posixpath.sep)
        yield posixpath.splitext(relpath)[0]


def write_sitemap(paths, base_url, output):
    dirname = os.path.dirname(output)
    if dirname and not os.path.isdir(dirname):
        os.makedirs(dirname)

    with open(output, 'w') as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for path in paths:
            out.write('  <url>\n')
            out.write('    <loc>%s</loc>\n' % escape(urljoin(base_url, path)))
            out.write('  </url>\n')
        out.write('</urlset>\n')


def main(argv):
    parser = argparse.ArgumentParser(description='Generate sitemap.xml for the static site.')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL)
    parser.add_argument('--content-dir', default=DEFAULT_CONTENT_DIR)
    parser.add_argument('--output', default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    write_sitemap(source_paths(args.content_dir), args.base_url, args.output)


if __name__ == '__main__':
    main(sys.argv[1:])
