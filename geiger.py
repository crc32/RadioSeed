#!/usr/bin/env python
# minimal geigercounter
# Modified from https://apollo.open-resource.org/mission:log:2014:06:13:generating-entropy-from-radioactive-decay-with-pigi

 
import time
import threading
import random
 
try:
    import RPi.GPIO as GPIO
    geiger_simulate = False
except ImportError:
    print("Simulating")
    geiger_simulate = True
         
GPIO_PIGI = 18
SIM_PER_SEC = 10000
 
class GeigerCounter():
    def __init__(self):
        self.tick_counter = 0
             
        self.geiger_simulate = geiger_simulate
        if self.geiger_simulate:
            self.simulator = threading.Thread(target=self.simulate_ticking)
            self.simulator.daemon = True
            self.simulator.start()
        else:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(GPIO_PIGI,GPIO.IN)
            GPIO.add_event_detect(GPIO_PIGI,GPIO.FALLING)
            GPIO.add_event_callback(GPIO_PIGI,self.tick)
         
    def simulate_ticking(self):
        while True:
            time.sleep(random.random()/(2*SIM_PER_SEC))
            self.tick()
     
    def tick (self,pin=0):
        self.tick_counter += 1
        print("Ticks: %d"%self.tick_counter)

    def isSimulation(self):
        if self.geiger_simulate:
            return "This is a SIMULATED run."
        else:
            return "LIVE RUN with PI Geiger Counter."
 
if __name__ == "__main__":
    gc = GeigerCounter()
    while True:
        time.sleep(1)
