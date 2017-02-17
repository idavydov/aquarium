#!/bin/bash
#hugo
#rm -Rf public/
rsync -av --delete --recursive --exclude '*~' static/ public
mkdir public/аккорды
bin/gen_static.py
rsync -avz --delete --recursive -e ssh public/ qc:aquarium
