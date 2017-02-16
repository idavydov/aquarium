#!/bin/bash
#hugo
rm -Rf public/
rsync -delete --exclude '*~' static/ public/
mkdir public/аккорды
bin/gen_static.py
rsync -avz -delete -e ssh public/ qc:aquarium
