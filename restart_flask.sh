#!/bin/bash

until python app.py; do
    echo "'app.py' crashed with exit code $?. Restarting..." >&2
    sleep 1
done

