#!/bin/bash
start_time=$(date +%s)
start_time=$((start_time+5))
ssh distrib-1 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client1 room=chatroom mode=fifo msgfile=messages/long_message.txt start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-2 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client2 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-3 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client3 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-4 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client4 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-5 "echo $start_time && cd distrib && bash run_client.sh udp=5001 register=client5 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-1 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client6 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-2 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client7 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-3 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client8 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-4 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client9 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-5 "echo $start_time && cd distrib && bash run_client.sh udp=5002 register=client10 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-1 "echo $start_time && cd distrib && bash run_client.sh udp=5003 register=client11 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-2 "echo $start_time && cd distrib && bash run_client.sh udp=5003 register=client12 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-3 "echo $start_time && cd distrib && bash run_client.sh udp=5003 register=client13 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-4 "echo $start_time && cd distrib && bash run_client.sh udp=5003 register=client14 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-5 "echo $start_time && cd distrib && bash run_client.sh udp=5003 register=client15 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null &
ssh distrib-1 "echo $start_time && cd distrib && bash run_client.sh udp=5004 register=client16 room=chatroom mode=fifo start=$start_time benchname=bench-16 server=distrib-4:5000" > /dev/null
