#!/usr/bin/env python
## remove newlines
import sys
import re

sspace = re.compile('^ *')
nlsp = re.compile('[\n ]+')

out = ''
body = False
for line in open(sys.argv[1]):
    if not body:
        if '<body' in line:
            body = True
        print line,
        continue

    out += ' ' + line[:-1]
    if out.endswith('>'):
        out = sspace.sub('', out)
        out = nlsp.sub(' ', out)
        print out
        out = ''
    
