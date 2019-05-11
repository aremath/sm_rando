#!/bin/bash
todofile="output/todos.txt"
isn=false
while getopts "n" opt; do
    case $opt in
        n)
            isn=true;
    esac
done
f=$(find . -type f ! -path "./.git*" ! -path "*pycache*" ! -path "*ipynb*" ! -path "*.swp" ! -path "*todos.txt")
g=$(grep -nT "TODO" $f)
if $isn; then
    wc -l <<< "$g"
else
    echo "$g" > $todofile
fi
