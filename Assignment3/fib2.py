#! /usr/bin/python

import time
import sys
import ctypes

libCycleTime = ctypes.CDLL("./cycletimelib/libCycleTime.so")

def recur_fibo(n):
   if n <= 1:
       return n
   else:
       return(recur_fibo(n-1) + recur_fibo(n-2))

def trial(fib_cnt:int):
    libCycleTime.init_counters(1,1)
    before_c = libCycleTime.get_cyclecount()
    before_t = time.time()
    recur_fibo(fib_cnt)
    after_t = time.time()
    after_c = libCycleTime.get_cyclecount()
    return (after_t-before_t, after_c-before_c)

if len(sys.argv)>1:
   nterms = int(sys.argv[1])
# Program to calculate the Fibonacci sequence up to n-th term
else:
   nterms = int(input("How many terms? "))



# check if the number of terms is valid
if nterms <= 0:
   print("Please enter a positive integer")
else:
   recur_fibo(nterms)

time_t, time_c = trial(nterms)
print(f"python time: {time_t}, cycle count: {time_c}")
