#!/usr/bin/env python
# -*- coding: utf8 -*-
import glob
import os.path
import codecs
import json
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape, meta

env = Environment(
    loader=FileSystemLoader(('templates/', 'content/')),
    autoescape=select_autoescape(['html', 'xml'])
)

outdir = 'public/'
indir = 'content/'
canonical_base = 'https://aquarium.rifma.ch/'

chords = []
for fn in sorted(glob.glob(indir + 'аккорды/*.html')):
    bn = fn.lstrip(indir)

    tmpl = env.get_template(bn)
    title = tmpl.module.title
    try:
        extra_title = ' ' + tmpl.module.extra_title
    except AttributeError:
        extra_title = ''

    path = bn.rsplit('.', 1)[0]
    canonical_url = canonical_base + quote(path, safe='/')
    out = codecs.open(os.path.join(outdir, path),
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
