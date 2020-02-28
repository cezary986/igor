import sys
sys.path.append('../../')
import os
from igor.server import IgorServer, CONFIG
from threading import Thread
import time


IGOR_CONFIG = CONFIG

CONFIG['file_server_config'] = {
        'enable': True,
        'port': 8080,
        'root_directory': os.path.dirname(__file__)
    }


def echo(out, data, **kwargs):
    out.send(data)

def test_introduce_self(out, data, **kwargs):
    out.send(kwargs['session'])

ACTIONS = {
    'echo': echo
}

class BacgroundProcess(Thread):
     def __init__(self):
         Thread.__init__(self)
         self.scope = None # will be populated by igor server
         self.process_id = None # will be populated by igor server
         self.output = None # will be populated by igor server
         self.counter = 0

     def run(self):
        while True:
            time.sleep(1)
            self.counter = self.counter + 1
            
            self.output.send('tick', 'tack')
            try:
                self.output.send('tick', 'special_for_CLIENT_1', client_id='CLIENT_1')
            except Exception:
                pass
            


igor = IgorServer(api=ACTIONS)
igor.add_process('test_process', BacgroundProcess())
igor.run_forever()
