#!/bin/bash

ssh distrib-1 "pkill -f source/client/client.py"
ssh distrib-2 "pkill -f source/client/client.py"
ssh distrib-3 "pkill -f source/client/client.py"
ssh distrib-4 "pkill -f source/client/client.py"
ssh distrib-5 "pkill -f source/client/client.py"