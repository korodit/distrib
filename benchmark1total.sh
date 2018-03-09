#!/bin/bash
start_time=$(date +%s)
start_time=$((start_time+5))
ssh -tt distrib-1 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client1 room=chatroom mode=total msgfile=messages/messages1.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh -tt distrib-2 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client2 room=chatroom mode=total msgfile=messages/messages2.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh -tt distrib-3 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client3 room=chatroom mode=total msgfile=messages/messages3.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh -tt distrib-4 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client4 room=chatroom mode=total msgfile=messages/messages4.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh -tt distrib-5 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client5 room=chatroom mode=total msgfile=messages/messages5.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null
