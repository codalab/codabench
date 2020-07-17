#!/usr/bin/env bash
# A small script for running selenium tests repeatedly.

for i in $(seq 1 $2)
do
    ./run_selenium_tests.sh -k $1 --create-db
done
