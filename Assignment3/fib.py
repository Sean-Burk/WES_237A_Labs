#! /usr/bin/python

import time
import sys


if len(sys.argv)>1:
   nterms = int(sys.argv[1])
# Program to calculate the Fibonacci sequence up to n-th term
else:
   nterms = int(input("How many terms? "))

def recur_fibo(n):
   if n <= 1:
       return n
   else:
       return(recur_fibo(n-1) + recur_fibo(n-2))

tic = time.time()

# check if the number of terms is valid
if nterms <= 0:
   print("Please enter a positive integer")
else:
   recur_fibo(nterms)
        
tac = time.time()
print('time spent: {}'.format(tac-tic))
