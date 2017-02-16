#!/usr/bin/env python
# -*- coding: utf8 -*-
import glob
import os.path
import codecs
import json

def set_tracking(s):
    return s.replace('{{tracking}}',
                     tracking)

def get_header(f):
    started = False
    d = {}
    for line in f:
        if line.strip() == '+++':
            if started:
                return d
            else:
                started = True
            continue
        else:
            if line.strip():
                k, v = line.split('=')
                k = k.strip()
                v = json.loads(v)
                d[k] = v


tracking = codecs.open('templates/tracking.html', 'r', 'utf8').read()
chords_template = codecs.open('templates/chords.html', 'r', 'utf8').read()
chords_template = set_tracking(chords_template)
index_template = codecs.open('templates/index.html', 'r', 'utf8').read()
index_template = set_tracking(index_template)
footer = codecs.open('layouts/partials/footer.html', 'r', 'utf8').read()
outdir = 'public/'

links = []

for fn in sorted(glob.glob('content/аккорды/*.html')):
    f = codecs.open(fn, 'r', 'utf8')
    h = get_header(f)
    fn = os.path.basename(fn).rsplit('.', 1)[0].decode('utf8')
    outfn = os.path.join(outdir, u'аккорды', fn)
    out = codecs.open(outfn, 'w', 'utf8')
    if 'handbook_unid' in h:
        handbook = u'<br/>\n<a href="http://handbook.severov.net/handbook.nsf/1/%s">%s в справочнике</a><br/>\n' % (
            h['handbook_unid'], h['title'])
    else:
        handbook = ''

    out.write(chords_template.replace('{{Title}}', h['title']) % (f.read(), handbook))
    f.close()
    link = u'<p><a href="%s">%s</a> %s</p>' % (
        u'аккорды/' + fn, h['title'], h.get('extra_title', u''))
    links.append(link)

half = (len(links) + 1) / 2
index = codecs.open(os.path.join(outdir, 'index.html'), 'w', 'utf8')
index.write(index_template % (
    '\n'.join(links[:half]), '\n'.join(links[half:])
))
index.close()
