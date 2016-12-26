#!/bin/bash
n=$(ls songs/*.htm | wc -l)
n=$(expr $n + 1 / 2)
i=0
for fn in songs/*.htm
do
    name=$(basename "$fn")
    name=${name%.*}
    if [ "$i" -eq "$n" ]
    then
	echo "</div>"
	echo 
        echo '<div class="col-lg-6">'
    fi
    echo "<p><a href=\"$fn\">$name</a></p>"
    ((i++))
    
done
