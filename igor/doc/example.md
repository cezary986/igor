# Example

Below you can see a simple example of usage, covering most of the features.
There is an API specified by `ACTIONS` dictionary. Actions handlers are in a different file (`events.py`). There is also a proccess `counter_process` which runs in the background, inceremnting counter every second and sending its value to all clients. Additionally there is a file server enables which gives clients easy way to read and write files.

`main.py`
```python
from endpoints.events import get_events, add_event, delete_event, update_event
import os
from igor.server import IgorServer
import json
from threading import Thread
import time
from igor.server import CONFIG

IGOR_CONFIG = CONFIG
CONFIG['port'] = 5000
# Enable file server
CONFIG['file_server'] = True

ACTIONS = {
    'get_events': get_events,
    'add_event': add_event,
    'delete_event': delete_event,
    'update_event': update_event
}

class BacgroundProcess(Thread):
     def __init__(self):
         Thread.__init__(self)
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

```

This file is just example and isn't the best way or practices to save data
`events.py`
```python
import json
import uuid
import os

EVENTS_FILE_NAME = 'events.json'

def read_events():
    with open(EVENTS_FILE_NAME, 'r') as file:
        return json.load(file)

def save_events(events):
    with open(EVENTS_FILE_NAME, 'w+') as outfile:
        json.dump(events, outfile)

def get_events(out, data):
    events_dictionary = read_events()
    out.send(list(events_dictionary.values()))

def add_event(out, event):
    events = read_events()
    id = str(uuid.uuid4())
    event['id'] = id
    events[id] = event
    save_events(events)
    out.send()

def delete_event(out, event_uuid):
    events = read_events()
    if event_uuid in events:
        del events[event_uuid]
    save_events(events)
    out.send()

def update_event(out, event):
    events = read_events()
    if event.uuid in events:
        events[event.uuid] = event
    save_events(events)
    out.send()

```