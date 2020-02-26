from endpoints.greeting import hello, bye
from endpoints.events import get_events, add_event, delete_event, update_event
import os
from igor.server import IgorServer
import os 
import json
from threading import Thread
import time

from igor.server import CONFIG

IGOR_CONFIG = CONFIG

CONFIG['file_server'] = True

def test(out, data, **kwargs):
    out.send('TEST' + data)

ACTIONS = {
    'test': test,
}

class BacgroundProcess(Thread):
     def __init__(self):
         Thread.__init__(self)
         self.scope = None # will be populated by igor server
         self.process_id = None # will be populated by igor server
         self.output = None # will be populated by igor server
         self.counter = 0

     def run(self):
        print('BacgroundProcess run')
        while True:
            time.sleep(1)
            self.counter = self.counter + 1
            
            self.output.send('counter_increment', {'counter': self.counter})


igor = IgorServer(api=ACTIONS)
igor.add_process('counter_process', BacgroundProcess())
igor.run_forever()
