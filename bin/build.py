#!/usr/bin/env python3
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    os.chdir(Path(__file__).resolve().parent.parent)
    # public/ is generated; clear it so removed pages and old routes cannot linger.
    if Path('public').exists():
        shutil.rmtree('public')
    shutil.copytree('static', 'public')
    subprocess.run([sys.executable, 'bin/gen_static.py', '--html'], check=True)
    subprocess.run([sys.executable, 'bin/gen_sitemap.py'], check=True)


if __name__ == '__main__':
    main()
