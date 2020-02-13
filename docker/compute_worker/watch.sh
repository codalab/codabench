#!/bin/sh
watchmedo shell-command --patterns="*.html" \
                        --recursive \
                        --command="python /app/put_detailed_results.py '$1' '$2' '$3'" \
                        $4
