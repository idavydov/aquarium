#!/usr/bin/env python
import sys
from bs4 import BeautifulSoup, Comment

def fxst(s):
    s = s.strip()
    s = s.replace('\n', '').replace('\r', '')
    try:
        a, b = s.split(':')
    except ValueError:
        print >> sys.stderr, 'bad style "%s" in %s' % (s, sys.argv[1])
        return s
    return ':'.join((a.strip(), b.strip()))

soup = BeautifulSoup(open(sys.argv[1]), 'lxml')

## remove extra attributes from html
html = soup.find("html")
try:
    html.attrs = {}
except:
    print >> sys.stderr, 'err finding html in %s' % sys.argv[1]

for meta in soup.findAll('meta'):
    meta.extract()

for link in soup.findAll('link'):
    link.extract()


# remove iframes
for element in soup.findAll('iframe'):
    element.extract()

usedstyles = set()
badstyles = set(('font-family:"Courier New"', 'color:black',
                 'layout-grid-mode:line', 'mso-pagination:none',
                 'mso-spacerun:yes', 'mso-ansi-language:EN-US',
                 'mso-tab-count:1', 'mso-tab-count:2',
                 'mso-tab-count:3', 'mso-bidi-font-weight:normal',
                 'mso-ansi-language:DE', 'text-justify-trim',
                 'font-size:10.0pt', 'tab-stops', 'tab-interval'))

try:
    soup.find("style").extract()
except:
    print >> sys.stderr, 'error finding style in %s' % sys.argv[1]



# remove comments
for element in soup(text=lambda text: isinstance(text, Comment)):
    element.extract()

for element in soup.findAll():
    del element['class']
    
# for element in soup.findAll('p', class_='MsoNormal'):
#     del element['class']

# for element in soup.findAll('span', class_='SpellE'):
#     del element['class']

# for element in soup.findAll('span', class_='GramE'):
#     del element['class']

# replace h1 with i
for element in soup.findAll('h1'):
    element.name = 'i'

for element in soup.findAll('o:p'):
    element.replaceWithChildren()
for element in soup(style=True):
    styles = [fxst(e) for e in element['style'].split(";")]
    styles = [e for e in styles if e and e not in badstyles and e.split(':')[0] not in badstyles]
    styles = [e for e in styles if not e.startswith('mso-')]
    usedstyles.update(styles)
    if styles:
        element['style'] = ';'.join(styles)
    else:
        del element['style']

for element in soup(lang=True):
    del element['lang']

for span in soup('span'):
    if not span.attrs:
        span.replaceWithChildren()

for div in soup('div'):
    if not div.attrs:
        div.replaceWithChildren()

# replace p with br
for p in soup('p'):
    br = soup.new_tag('br')
    idx = p.parent.contents.index(p)
    p.parent.insert(idx + 1, br)
    p.replaceWithChildren()

for pre in soup('pre'):
    br = soup.new_tag('br')
    idx = pre.parent.contents.index(pre)
    pre.parent.insert(idx + 1, br)
    pre.replaceWithChildren()


#for element in soup(style=True):
#    print element['style']

body = soup.find('body')
body['style'] = body.get('style', '')
if body['style'] != '':
    body['style'] += ';'
body['style'] += 'font-family:"Courier New",monospace'
body['style'] += ';font-size:10.0pt'

print str(soup)

with open('usedstyles', 'a') as f:
    for e in usedstyles:
        print >> f, e
