#!/bin/bash
start_time=$(date +%s)
start_time=$((start_time+5))
ssh distrib-1 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client1 room=chatroom mode=total msgfile=messages/long_message.txt start=$start_time benchname=bench-4 server=distrib-4:5000" > /dev/null &
ssh distrib-2 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client2 room=chatroom mode=total start=$start_time benchname=bench-4 server=distrib-4:5000" > /dev/null &
ssh distrib-3 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client3 room=chatroom mode=total start=$start_time benchname=bench-4 server=distrib-4:5000" > /dev/null &
ssh distrib-4 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client4 room=chatroom mode=total start=$start_time benchname=bench-4 server=distrib-4:5000" > /dev/null