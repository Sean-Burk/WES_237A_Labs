import threading
from enum import IntEnum
import time
import random


def led_on_ex(id):
    if id<=3:
        base.leds[id].on
    elif id==4:
        rgbled.RGBLED(4).on(2)

def led_off_ex(id):
    if id<=3:
        base.leds[id].off
    elif id==4:
        rgbled.RGBLED(4).off()

def blink_for_duration(duty, rate, duration, led_id):
    start=time.time()
    while start+duration>time.time():
        led_on_ex(led_id)
        time.sleep((1/rate)*(duty/100.0))
        led_off_ex(led_id)
        time.sleep((1/rate)-(1/rate)*(duty/100.0))


# state wait durations
NAP_DUR = 4
EAT_DUR = 2
# Philosopher/fork count
PHIL_CNT = 5

class PhilosopherStates(IntEnum):
    STARVING = 0
    EATING = 1
    NAPPING = 2

class Philosopher:
    def __init__(self, id, forks:list[threading.Lock]):
        self.state = PhilosopherStates.STARVING
        # id number to keep track of what forks are adjacent and led id
        self.id = id 
        # get the correct forks for this philosopher
        self.right_fork=forks[(id+1)%PHIL_CNT]
        self.left_fork=forks[id]

        # state dict
        self.state_dict = {
            PhilosopherStates.STARVING: self.starving,
            PhilosopherStates.EATING: self.eating,
            PhilosopherStates.NAPPING: self.napping
        }

    def run(self, exit:threading.Event):
        while not exit.is_set():
            new_state = self.state_dict[self.state]()
            if new_state != self.state:
                print(f"State tranistion {self.state.name}->{new_state.name}")
            self.state = new_state

    def starving(self):
        # don't blink and try to aquire forks to eat
        if self.right_fork.acquire(blocking=False):
            if self.left_fork.acquire(blocking=False):
                # we have both forks time to eat
                return PhilosopherStates.EATING
            else:
                # we got right but not left so we need to give up the left to prevent blocking
                self.right_fork.release()
        # Failed to acquire forks sleep and try again
        time.sleep(0.5)
        return PhilosopherStates.STARVING

    def eating(self):
        # blink at high rate wait and release forks
        # I should already have the forks
        blink_for_duration(20, 4, random.uniform(EAT_DUR, EAT_DUR+1), self.id)
        # give up forks
        self.right_fork.release()
        self.left_fork.release()
        # go to napping
        return PhilosopherStates.NAPPING

    def napping(self):
        # blink at low rate for napping and wait
        blink_for_duration(20, 2, random.uniform(NAP_DUR, NAP_DUR+1), self.id)
        # go to starving
        return PhilosopherStates.STARVING


def check_exit(exit:threading.Event):
    btns = base.btns_gpio
    while not exit.is_set():
        res = btns.read()
        if res != 0:
            exit.set()
        time.sleep(0.1)
        


forks = [ threading.Lock() for i in range(PHIL_CNT) ]
philosophers = [ Philosopher(i, forks) for i in range(PHIL_CNT) ]
exit_event = threading.Event()
threads = [ threading.Thread(target=philosophers[i].run, args=(exit_event,)) for i in range(PHIL_CNT) ]
threads.append(threading.Thread(target=check_exit, args=(exit_event,)))
for t in threads:
    t.start()

for t in threads:
    t.join()
