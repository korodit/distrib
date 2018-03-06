#!/bin/bash
export LC_ALL=C
pip install --user virtualenv
virtualenv source/server/server_venv
. source/server/server_venv/bin/activate
pip install Flask
deactivate
virtualenv -p /usr/bin/python3 source/client/client_venv
. source/client/client_venv/bin/activate
pip install pqdict
deactivate