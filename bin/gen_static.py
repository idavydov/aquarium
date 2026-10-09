#!/usr/bin/env python
# -*- coding: utf8 -*-
import glob
import os.path
import codecs
import json
import argparse
import hashlib
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape, meta
from song_layout import apostrophes, song_context, song_layout

env = Environment(
    loader=FileSystemLoader(('templates/', 'content/')),
    autoescape=select_autoescape(['html', 'xml'])
)
env.filters['song_layout'] = song_layout
env.filters['song_context'] = song_context
env.globals['asset_version'] = hashlib.sha256(
    Path('static/css/archive.css').read_bytes() + Path('static/js/archive.js').read_bytes()
).hexdigest()[:12]

outdir = 'public/'
indir = 'content/'
canonical_base = 'https://aquarium.rifma.ch/'

parser = argparse.ArgumentParser(description='Render the static chord archive.')
parser.add_argument('--html', action='store_true',
                    help='Write .html files for extensionless Cloudflare Pages routes.')
args = parser.parse_args()
chord_outdir = os.path.join(outdir, 'аккорды')
if not os.path.isdir(chord_outdir):
    os.makedirs(chord_outdir)

chords = []
for fn in sorted(glob.glob(indir + 'аккорды/*.html')):
    bn = os.path.relpath(fn, indir)

    tmpl = env.get_template(bn)
    title = apostrophes(tmpl.module.title)
    try:
        extra_title = ' ' + tmpl.module.extra_title
    except AttributeError:
        extra_title = ''

    path = bn.rsplit('.', 1)[0]
    chords.append({'title': title,
                   'extra_title': extra_title,
                   'url': '/' + path,
                   'template': bn})

chords = sorted(chords, key=lambda e: e['title'])
for chord in chords:
    path = chord['url'].lstrip('/')
    filename = path + '.html' if args.html else path
    with codecs.open(os.path.join(outdir, filename), 'w', 'utf8') as out:
        out.write(env.get_template(chord['template']).render(
            display_title=chord['title'],
            canonical_url=canonical_base + path))

tmpl = env.get_template('index.html')

out = codecs.open(os.path.join(outdir, 'index.html'),
        'w', 'utf8')
out.write(tmpl.render(chords=chords,
                      canonical_url=canonical_base))
out.close()
