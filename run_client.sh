#!/bin/bash
# gets one parameter, the UDP listen port
. source/client/client_venv/bin/activate
python source/client/client.py $1
deactivate