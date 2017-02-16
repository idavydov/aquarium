#!/bin/bash
outdir=$1
for f in аккорды/*
do
    ln -s -- "$f" x.html
    phantomjs /usr/share/doc/phantomjs/examples/rasterize.js file://$(pwd)/x.html "$outdir/$(basename $f)".png
    rm -f x.html
done
