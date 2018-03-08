#!/bin/bash
. source/server/server_venv/bin/activate
export FLASK_APP=source/server/server.py
export FLASK_DEBUG=0
flask run --host=0.0.0.0
deactivate