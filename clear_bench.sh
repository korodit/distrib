#!/bin/bash

ssh distrib-1 "rm /home/distrib04/distrib/benchmarks/* && echo . > /home/distrib04/distrib/benchmarks/dummy_placeholder.txt"
ssh distrib-2 "rm /home/distrib04/distrib/benchmarks/* && echo . > /home/distrib04/distrib/benchmarks/dummy_placeholder.txt"
ssh distrib-3 "rm /home/distrib04/distrib/benchmarks/* && echo . > /home/distrib04/distrib/benchmarks/dummy_placeholder.txt"
ssh distrib-4 "rm /home/distrib04/distrib/benchmarks/* && echo . > /home/distrib04/distrib/benchmarks/dummy_placeholder.txt"
ssh distrib-5 "rm /home/distrib04/distrib/benchmarks/* && echo . > /home/distrib04/distrib/benchmarks/dummy_placeholder.txt"