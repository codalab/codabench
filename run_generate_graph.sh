#!/usr/bin/env bash
#Uses graphviz to convert .dot to .png

#Kwargs**: [FILENAME] [APPS...]
#Ex: run_generate_graph.sh filename
#Ex: run_generate_graph.sh filename model1 model2...

mkdir "graphs"

if [ -z "$1" ]; then
    docker-compose exec django ./manage.py graph_models -a > ./graphs/graph.dot
    dot -Tpng ./graphs/graph.dot -o ./graphs/graph.png
else
    filename=$1
    shift
    if [ -z "$1" ]; then
        docker-compose exec django ./manage.py graph_models -a > "./graphs/$filename.dot"
    else
        docker-compose exec django ./manage.py graph_models "$@" > "./graphs/$filename.dot"
    fi
    dot -Tpng "./graphs/$filename.dot" -o "./graphs/$filename.png"
fi
