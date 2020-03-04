# Igor

Simple solution fo integrating python and modern web-based desktop apps e.g build using Elector.

Igor consists of two main parts:
* server - it provides your clients processes with easy access to your python API.
* clients - your non-pythonic application, for example rendered processs in Electron.

Igor's using websockets for communiection which gives you easy and bideractional communication beetween your client and python backend. 

## Instalation

```bash
pip install -e git+https://github.com/cezary986/igor#egg=igor
```

## Creating API
Usage of this module is quite easy. First you need some Python API for your clients.
To make an API from you code you need to create a dictionary object with a following structure:

```python
API = {
  'action_identifier': action_handler_function,
  ... 
}
```

Your API object could be a nested dictionary too but before passing it to Igor you need to flatten it with `flatten` function:

```python
from igor.core import flatten

API = {
    'events': {
        'create': create_event,
        'remove': remove_event,
        'update': update_event, 
    }
    ...   
}

server = IgorServer(api=flatten(API))
```

Such code will flatten your dictionary merging it fields names with default separator `.` So to access your `create_event`
function handler you now need to call action with id: `events.create` You can also change separator by passing `separator`
argument to `flatten` function.

Your handler function will be called by server each time any of your clients calls for certain action.
Example handler function can looks like this:

```python
def hello(out, event, **kwargs):
    name = data['name']
    out.send('Hello ' + name)
```
It allways takes three main parameters:
* output - stream object which allows you to send data back to client
* data - data object (dictionary) passed to you by client
* **kwargs - for some additional parametrs, described later

Igor server will populates those parameters for you each time calling handler.

## Starting server

In your main block of code you need to start your Igor server instance. Minimalistic example is shown below:
```python

server = IgorServer(api=API)
igor.run_forever()

```
This will start server with default port and host which is: `localhost:5678`. You can customize it be passing argument to the constructor:

```python

CONFIG = {
    'port': 6000,
}

server = IgorServer(api=API, config=CONFIG)
igor.run_forever()

```

To see all fields allowed in config dictionary see the `server.py` file

## Binding with UI process

Igor is intended to work as a kind of backend for desktop applications. It is therefore desirable for it to run only as long as the ui process. If you are using Electron
you may achieve it with a use of simple function handler:

In your python code:
```python
def shutdown_igor(out, data, **kwargs):
    sys.exit() # shutdown igor and whole Python program

ACTIONS = {
    ...
    'shutdown': shutdown_igor
}
```
Then you need to make sure that `shutdown` action will be called when user exit UI process. In Electron you can use `window-all-closed` event for this. In your `main.js`:
```js
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    // shutdown igor process
    const ws = new WebSocket('ws://127.0.0.1:5678');
    ws.on('open', function open() {
      ws.send(JSON.stringify({
        streamId: 'igor_shutdown',
        action: 'shutdown',
        data: null
      }));
      app.quit()
    });
  }
})
```

## Processes

Examples above only covers scenario when your client request some action from server. Another use case could be to have a certain `process` in your python code which will run independently and send some data to clients as it runs. This is possible to achieve by using so called `processes`. 

| processes are in fact implemented as Threads in Igor

To create background process you need your Thread class and its instance. Below is and example:

```python

class BacgroundProcess(Thread):
     def __init__(self):
         Thread.__init__(self)
         self.process_id = None # will be populated by server
         self.output = None # will be populated by server
         self.counter = 0

     def run(self):
        print('BacgroundProcess run')
        while True:
            time.sleep(1)
            self.counter = self.counter + 1
            # you can use output here because server populated it
            self.output.send(action='counter_increment', data={'counter': self.counter})


igor = IgorServer(api=ACTIONS)
igor.add_process('counter_process', BacgroundProcess())
igor.run_forever()
```

Process output object is different from handler output object. It allows you to send data the same way as function handler output (see example above), this will send data to every client connected to server. You can also send data to specific client using his id:

```python
def run(self):
  self.output.send('special_for_you', 'only_for_client_1', client_id=1)

```
## Usage in UI processes

To bind your program with Igor you can use created library for Angular 8+ or write own library.

Igor use websockets and creates a little abstraction over them called streams. If you are familiar with RxJs or RxJava Observables thats good, because stream works pretty much like them, but less complicated. By deafult websocket allows only single stream of date to be send in both directions. We can either create more sockets connections for different data (consume more resources) or use only one and write some custom code to create ilusion of having multiple streams - thats what Igor do. 

Each time action is being dispached new stream is created. It has its own unique id and lives till handler function finishes. Streams id's are generated by clients so unless you are using Angular library you need to handle generation of unique stream id's on your own. Good idea is to use either some counter or uuid algorithms. 

## Tests

All tests are in `igor.test` package, it is better to run them separately one by one especially `test_integration.py`

File `test_server.py` contains unit test for server class, `test_core.py` containts unit tests for core igor classes such as Streams. `test_integration.py` containt integrations test of the server.

> To run `test_integration.py` you need your virtualenv to be in the parent directory on the igor directory. If you don't you can change this fragment to match your virtualenv path:

```python
try:
    igor_process = subprocess.Popen('START ' + os.getcwd() + '\..\..\env\Scripts\python.exe server_instance.py', shell=True) # change here
except error:
    print('Unable to start igor server instance. Check if the port is not already in use')
```

