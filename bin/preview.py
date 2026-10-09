#!/usr/bin/env python3
"""Serve a local build with the archive's extensionless song URLs."""
import argparse
import random
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


PUBLIC = Path(__file__).resolve().parent.parent / 'public'


class Handler(SimpleHTTPRequestHandler):
    disable_js = False

    def end_headers(self):
        if urlsplit(self.path).path == '/r':
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Robots-Tag', 'noindex, nofollow')
        if self.disable_js:
            self.send_header('Content-Security-Policy', "script-src 'none'")
        super().end_headers()

    def do_GET(self):
        if urlsplit(self.path).path == '/r':
            self.serve_random()
            return
        path = self.translate_path(urlsplit(self.path).path)
        if not Path(path).exists() and Path(path + '.html').is_file():
            parts = urlsplit(self.path)
            self.path = parts.path + '.html' + ('?' + parts.query if parts.query else '')
        super().do_GET()

    def do_HEAD(self):
        if urlsplit(self.path).path == '/r':
            self.serve_random(head=True)
        else:
            super().do_HEAD()

    def serve_random(self, head=False):
        if parse_qs(urlsplit(self.path).query).get('r', [None])[0] != 'r':
            self.send_error(404)
            return
        song = random.choice(list((PUBLIC / 'аккорды').glob('*.html')))
        body = song.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def send_error(self, code, message=None, explain=None):
        if code == 404 and (PUBLIC / '404.html').is_file():
            body = (PUBLIC / '404.html').read_bytes()
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)
        else:
            super().send_error(code, message, explain)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-js', action='store_true',
                        help='Block scripts to check the static reading layout.')
    args = parser.parse_args()
    Handler.disable_js = args.no_js
    server = ThreadingHTTPServer(('127.0.0.1', args.port),
                                 partial(Handler, directory=str(PUBLIC)))
    print('Preview: http://127.0.0.1:%s' % args.port, flush=True)
    server.serve_forever()
