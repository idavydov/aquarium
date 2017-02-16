#!/usr/bin/env python
# -*- coding: utf8 -*-
import glob
import re

spbr = re.compile('^\s*<br/>\n?', re.UNICODE)
spbr_strict = re.compile('^ +<br/>\n?', re.UNICODE)

for fn in glob.iglob('content/аккорды/*.html'):
    lines = open(fn).readlines()

    for i in xrange(len(lines)):
        if i > 0:
            if lines[i - 1].endswith('<br/>\n'):
                if spbr.search(lines[i].decode('utf8')):
                    lines[i] = '<br/>\n'
        elif lines[i] == ' <br/>\n':
            if spbr_strict.search(lines[i].decode('utf8')):
                lines[i] = '<br/>\n'
    
    while spbr.search(lines[-1].decode('utf8')):
        lines = lines[:-1]
    # if not lines[-1].startswith('</table>'):
    #     print fn
    #     print ''.join(lines[-2:])
    out = open(fn, 'w')
    out.write(''.join(lines))
    out.close()
