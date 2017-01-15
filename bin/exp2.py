#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from BeautifulSoup import BeautifulSoup, UnicodeDammit, Tag

surl = 'http://separationend.narod.ru/'
baseurl = 'http://separationend.narod.ru/chords/html/'
basepath = 'separationend/chords/html/'

def correct_name(n):
    return n.replace(' ', '_').replace('/', '_').replace('?', '').replace(u'№', 'N').replace('`', "'").replace('"', "'").encode('utf-8')

def fix_spaces(n):
    if '(' in n:
        a, b = n.split('(', 1)
        n = a.rstrip() + ' (' + b
    e = [s.strip() for s in n.split(',')]
    return ', '.join(e)

def save_html(fn, name):
    try:
        with open(fn) as f:
            content = filter(lambda s: 'www.ucoz.ru' not in s, f.readlines())
            content = ''.join(content)
            content = content.replace('<body>', '<body><pre>')
            content = content.replace('</body>', '</pre></body>')
    except:
        print >> sys.stderr, 'Error reading file: %s, %s' % (fn, name)
        return

    dammit = UnicodeDammit(content, ["utf-8", "cp1251", "ISO-8859-1"])

    soup = BeautifulSoup(dammit.unicode, convertEntities=BeautifulSoup.ALL_ENTITIES)
    title = soup.find('title')
    title.string = u'%s - аккорды, Аквариум и Борис Гребенщиков (БГ)' % name

    # remove all scripts
    [s.extract() for s in soup('script')]

    # remove tns counter
    for div in soup.findAll('div', style=True):
        if 'www.tns-counter.ru' in div['style']:
            div.extract()

    head = soup.find('head')
    meta = Tag(soup, "meta")
    meta['http-equiv'] = "Content-type"
    meta['content'] = "text/html; charset=utf-8"
    head.insert(0, meta)

    ## remove ucoz
    #for div in soup.findAll('div', align=True):
    #    if 'www.ucoz.ru' in str(div):
    #        div.extract()

    for a in soup.findAll('a', href=True):
        if a['href'] == surl:
            a['href'] = '/'
        elif a['href'].startswith(surl):
            a.replaceWithChildren()
        else:
            print >> sys.stderr, fn, a['href']

    firstp = soup.find('p')
    if u'главная' not in str(firstp).decode('utf-8').lower():
            #print root, filename, 'main not found'
        print >> sys.stderr, 'cannot find main', fn, name
        print >> sys.stderr, firstp.getText()
    else:
        for span in firstp.findAll('span', style=True):
            if 'color:red' in span['style']:
                span['style'] = span['style'].replace('color:red;', '').replace('color:blue;', '')

    for img in soup.findAll('img', src=True):
        if img['src'].endswith('/partizany.bmp'):
            img['src'] = u'/img/партизаны.png'
        else:
            ## u_imperatora_nerona.bmp is lost :(
            img.extract()


    outname = 'аккорды/' + correct_name(name)
    with open(outname, 'w') as f:
        f.write(str(soup))
    return outname


soup = BeautifulSoup(open('separationend/abv.html'))
for div in soup.findAll('div', style=True):
    if 'display: none' not in div['style']:
        continue
    for a in div.findAll('a', href=True):
        name = fix_spaces(a.text)
        sib = a.nextSibling.strip()
        if sib:
            fullname = '%s %s' % (name, sib)
            sib = ' ' + sib
        if name == u'Новогоднее поздравление':
            name = fullname
            sib = ''
        url = a['href']
        assert url.startswith(baseurl)
        fn = url[len(baseurl):]
        n = save_html(basepath + fn, name)
        if n:
            n = n.decode('utf8')
            print (u'<p><a href="%s">%s</a>%s</p>' % (n, name, sib)).encode('utf8')
