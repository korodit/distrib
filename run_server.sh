#!/bin/bash
. venv/bin/activate
export FLASK_APP=source/server/server.py
export FLASK_DEBUG=1
flask run
deactivate