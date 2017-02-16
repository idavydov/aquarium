#!/bin/bash
hugo
rsync -avz -delete -e ssh public/ qc:aquarium
