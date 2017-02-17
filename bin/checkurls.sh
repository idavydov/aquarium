#!/bin/bash
sed -n '/aquarium[.]myths[.]ru/ s/.*,http/http/p' $1 | while read url
do
    response=$(curl -Is "$url" | head -1 | tr -d "\n\r")
    if [[ ! $response == "HTTP/1.1 200 OK" ]]
    then
	echo Problems with $url "($response)"
    fi
done
