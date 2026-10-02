#!/bin/bash
set -euo pipefail

deploy_target="${1:-${DEPLOY_TARGET:-}}"
rsync_path="${DEPLOY_RSYNC_PATH:-rsync}"

if [[ -z "$deploy_target" ]]
then
    echo "Usage: $0 user@host:/remote/path/"
    echo "For sudo-backed deploys: DEPLOY_RSYNC_PATH='sudo rsync' $0 user@host:/remote/path/"
    exit 2
fi

rsync -av --delete --recursive --exclude '*~' static/ public
mkdir -p public/аккорды
bin/gen_static.py
bin/gen_sitemap.py
rsync -avz --delete --recursive -e ssh --rsync-path="$rsync_path" public/ "$deploy_target"
