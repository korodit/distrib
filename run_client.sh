#!/bin/bash
# gets one parameter, the UDP listen port
. source/client/client_venv/bin/activate
# python source/client/client.py $1 $2 $3 $4
python source/client/client.py "$@"
deactivate