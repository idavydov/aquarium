#!/usr/bin/env python
import glob
from BeautifulSoup import BeautifulSoup

url = 'http://separationend.narod.ru/'
for fn in glob.glob('songs/*.htm'):
    with open(fn) as f:
        soup = BeautifulSoup(f)
    for a in soup.findAll('a', href=True):
        if a['href'] == url:
            a['href'] = '/'
        elif a['href'].startswith(url):
            a.replaceWithChildren()
        else:
            print fn, a['href']
    with open(fn, 'w') as f:
        f.write(soup.prettify('utf-8'))
