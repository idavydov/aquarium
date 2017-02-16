#!/bin/bash
for fn in $1/*;
do
    bn=$(basename $fn)
    hash1=$(identify -quiet -format "%#" "$fn")
    fn2="$2/$bn"
    hash2=$(identify -quiet -format "%#" -- "$fn2" 2>/dev/null)
    if [[ $hash1 != $hash2 ]]
    then
	reason=""
	test -f "$fn2" || reason="(file not found)"
	echo "mismatch in $bn $reason"
    fi
done	  
	  
