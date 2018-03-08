#!/bin/bash
# gets one parameter, the UDP listen port
. source/client/client_venv/bin/activate
# python source/client/client.py $1 $2 $3 $4
python source/client/client.py "$@"
deactivate
# bash run_client.sh udp=5006 register=orestarod room=loules mode=total/fifo msgfile=messages/messages1.txt start=1520531370.32 benchname=testbench server=distrib-1