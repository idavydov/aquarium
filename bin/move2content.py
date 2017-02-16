#!/usr/bin/python
# -*- coding: utf-8 -*-
## move to hugo structure
from datetime import date
import os.path
import csv
from bs4 import BeautifulSoup, Comment

def get_title_content(fn):
    soup = BeautifulSoup(open(fn), 'lxml')
    head = soup('head')[0]
    title = head('title')[0].text.rsplit('-', 1)[0][:-1]
    body = soup('body')[0]
    return title,''.join([e.encode('utf8') for e in body.contents])

def out(fn, name, extra, content):
    if extra:
        extra = extra.lstrip().replace('"', '\\"')
        extra = '\nextra_title = "%s"' % extra
    else:
        extra = ''
    un = ''
    if fn in fn2unid:
        un = '\nhandbook_unid = "%s"' % fn2unid[fn]
        del(fn2unid[fn])
    f = open(os.path.join(basepath, (fn + '.html').encode('utf8')), 'w')
    head = """+++
title = "%s"%s%s
date = "%s"

+++""" % (title.replace('"', '\\"'), extra, un, datestamp)
    f.write(head.encode('utf8'))
    f.write(content)
    f.close()

basepath = os.path.join('content', 'аккорды')
try:
    os.makedirs(basepath)
except OSError:
    pass

datestamp = date.today().isoformat()


fn2unid = {}
## first read csv
for record in csv.DictReader(open('handbook.csv')):
    fn = record['relative url'].decode('utf8')
    if fn:
        fn2unid[os.path.basename(fn)] = record['UNID']


soup = BeautifulSoup(open('index.html'), 'lxml')
for p in soup('p'):
    try:
        a = p('a')[0]
    except IndexError:
        continue
    name = a.text
    extra = a.next_sibling
    fn = a['href']
    title, content = get_title_content(fn)
    assert name == title
    out(os.path.basename(fn), name, extra, content)

assert len(fn2unid) == 0
