#!/bin/bash
line=$(grep -n '</head>' "$1" | cut -d ":" -f 1)
((line--))
sed -i "${line}r tracking" "$1"
