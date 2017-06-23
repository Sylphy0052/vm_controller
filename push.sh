#!/bin/bash

read -p "Input commit message : " message

git add .
git commit -m "$message"
git push
