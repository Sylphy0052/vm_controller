#!/bin/bash

ip=$1

while true
do
	echo "curl http://${ip}/index.html"
	curl http://${ip}/index.html
done