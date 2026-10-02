#!/usr/bin/env python
# -*- coding: utf8 -*-
import glob
import os.path
import codecs
import json
import argparse

from jinja2 import Environment, FileSystemLoader, select_autoescape, meta

env = Environment(
    loader=FileSystemLoader(('templates/', 'content/')),
    autoescape=select_autoescape(['html', 'xml'])
)

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
    title = tmpl.module.title
    try:
        extra_title = ' ' + tmpl.module.extra_title
    except AttributeError:
        extra_title = ''

    path = bn.rsplit('.', 1)[0]
    canonical_url = canonical_base + path
    filename = path + '.html' if args.html else path
    out = codecs.open(os.path.join(outdir, filename),
        'w', 'utf8')
    out.write(tmpl.render(canonical_url=canonical_url))
    out.close()
    chords.append({'title': title,
                   'extra_title': extra_title,
                   'url': '/' + path})

chords = sorted(chords, key=lambda e: e['title'])
half = (len(chords) + 1) // 2

tmpl = env.get_template('index.html')

out = codecs.open(os.path.join(outdir, 'index.html'),
        'w', 'utf8')
out.write(tmpl.render(chords1=chords[:half], chords2=chords[half:],
                      canonical_url=canonical_base))
out.close()
