#!/usr/bin/env python
# -*- coding: utf8 -*-
import glob
import sys
import json
import codecs



for fn in glob.iglob('content/аккорды/*.html'):
    lines = codecs.open(fn, 'r', 'utf8').readlines()
    assert lines[0] == '+++\n'
    lines = lines[1:]
    d = {}
    for i, line in enumerate(lines):
        if line == '+++\n':
            break
        else:
            if line.strip():
                k, v = line.split('=')
                k = k.strip()
                v = json.loads(v)
                d[k] = v
    else:
        print 'error couldnt find +++'
        sys.exit()
    lines = lines[i+1:]
    f = codecs.open(fn, 'w', 'utf8')
    print >> f, '{% extends "chords.html" %}'
    print >> f
    for k in ('title', 'extra_title', 'handbook_unid'):
        if k in d:
            print >> f, '{%% set %s = %s %%}' % (k, json.dumps(d[k], ensure_ascii=False))
    print >> f
    print >> f, '{% block content %}'
    print >> f, '{% raw %}'
    print >> f, ''.join(lines),
    print >> f, '{% endraw %}'
    print >> f, '{% endblock %}'
