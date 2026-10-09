#!/usr/bin/env python3
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import quote


def main():
    os.chdir(Path(__file__).resolve().parent.parent)
    # public/ is generated; clear it so removed pages and old routes cannot linger.
    if Path('public').exists():
        shutil.rmtree('public')
    shutil.copytree('static', 'public')
    subprocess.run([sys.executable, 'bin/gen_static.py', '--html'], check=True)
    subprocess.run([sys.executable, 'bin/gen_sitemap.py'], check=True)
    songs = [quote('/аккорды/' + path.stem) for path in sorted(Path('public/аккорды').glob('*.html'))]
    worker = Path('bin/random_worker.mjs').read_text(encoding='utf8')
    worker += '\nexport default createRandomWorker(%s);\n' % json.dumps(songs, ensure_ascii=False)
    Path('public/_worker.js').write_text(worker, encoding='utf8')


if __name__ == '__main__':
    main()
