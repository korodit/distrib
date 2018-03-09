#!/bin/bash
start_time=$(date +%s)
start_time=$((start_time+5))
ssh distrib-1 "echo $start_time && cd distrib && bash run_client.sh udp=5000 register=client1 room=chatroom mode=fifo msgfile=messages/messages1.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh distrib-2 "echo $start_time && cd distrib && bash run_client.sh udp=5000 register=client2 room=chatroom mode=fifo msgfile=messages/messages2.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh distrib-3 "echo $start_time && cd distrib && bash run_client.sh udp=5000 register=client3 room=chatroom mode=fifo msgfile=messages/messages3.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh distrib-4 "echo $start_time && cd distrib && bash run_client.sh udp=5000 register=client4 room=chatroom mode=fifo msgfile=messages/messages4.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null &
ssh distrib-5 "echo $start_time && cd distrib && bash run_client.sh udp=5000 register=client5 room=chatroom mode=fifo msgfile=messages/messages5.txt start=$start_time benchname=bench-1 server=distrib-4:5000" > /dev/null 
