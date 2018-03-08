#!/bin/bash
start_time=$(date +%s)
start_time=$((start_time+5))
echo $start_time
bash run_client.sh udp=5006 register=orestarod room=loules mode=total msgfile=messages/messages1.txt start=$start_time benchname=testbench