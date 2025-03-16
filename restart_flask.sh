#!/bin/bash

until waitress-serve --host=0.0.0.0 --port=80 app:app; do
    echo "'app.py' crashed with exit code $?. Restarting..." >&2
    sleep 1
done

