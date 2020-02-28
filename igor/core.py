import json
import logging
from threading import Thread


def flatten(api_dictionary, separator='.'):
    """
    Flatten nested API dictionary. If merge keys of each nested level with given
    separator - default is '.'

    :param api_dictionary: nested api dictionary object with handlers
    :param separator: string with which dictionary keys will be merges, default is '.'
    :return: flattened dictionary with only one level of nest
    """
    for key, value in list(api_dictionary.items()):
        if type(value) == dict:
            flatten(value)
            api_dictionary.pop(key)
            for key_2, value_2 in value.items():
                api_dictionary[key + separator + key_2] = value_2
    return api_dictionary

class Stream:

    def __init__(self, igor_server, client, stream_id, on_close_callback):
        self.client = client
        self.__igor_server = igor_server
        self.__on_close_callback = on_close_callback
        self.stream_id = stream_id
        self.closed = False

    def send(self, data=None):
        if self.closed:
            raise Exception('Cannot write to closed stream')
        serialized_message = json.dumps({
            'streamId': self.stream_id,
            'data': data
        })
        self.__igor_server.server.send_message(self.client, serialized_message)

    def send_error(self, error):
        if self.closed:
            raise Exception('Cannot write to closed stream')
        serialized_message = json.dumps({
            'streamId': self.stream_id,
            'error': str(error)
        })
        self.__igor_server.server.send_message(self.client, serialized_message)

    def close(self):
        if self.closed:
            raise Exception('Stream already closed')
        self.closed = True
        self.__igor_server.server.send_message(self.client, json.dumps({
            'streamId': self.stream_id,
            'close': True
        }))
        self.__on_close_callback(self.__igor_server, self.stream_id)

class ProcessOutput:
    """
    Output stream class for processes
    """

    def __init__(self, process_id, igor_server, on_finish_callback):
        self.__igor_server = igor_server
        self.process_id = process_id
        self.on_message_received = lambda *args: None
        self.__on_finish_callback = on_finish_callback
        self.closed = False

    def send(self, action, data=None, client_id=None):
        if self.closed:
            raise Exception('Cannot write to closed output')
        serialized_message = json.dumps({
            'streamId': self.process_id,
            'action': action, 
            'data': data
        })
        if client_id == None:
            self.__igor_server.server.send_message_to_all(serialized_message)
        else:
            client = self.__igor_server.clients.get(client_id, None)
            if client == None:
                raise Exception('No client with given id exist. Id= "' + client_id + '"')
            else:
                self.__igor_server.server.send_message(client, serialized_message)

    def send_error(self, error, client_id=None):
        if self.closed:
            raise Exception('Cannot write to closed output')
        serialized_message = json.dumps({
            'streamId': self.process_id,
            'error': str(error)
        })
        if client_id is None:
            self.__igor_server.server.send_message_to_all(serialized_message)
        else:
            client = self.__igor_server.clients.get(client_id, None)
            if client is None:
                raise Exception('No client with given id exist. Id= "' + client_id + '"')
            else:
                self.__igor_server.server.send_message(client, serialized_message)

    def finish(self):
        if self.closed:
            raise Exception('Output already closed')
        self.closed = True
        self.__igor_server.server.send_message_to_all(json.dumps({
            'streamId': self.process_id,
            'close': True
        }))
        self.__on_finish_callback(self.__igor_server, self.process_id)


async def handler_wrapper(handler_function, stream, data, session, scope):
    """
    Wrapper around handler function. Automatically closes stream and handles errors
    """
    try:
       handler_function(stream, data, session=session, scope=scope)
       stream.close()
    except Exception as error:
        logging.error(error)
        stream.send_error(str(error))
        stream.close()
        raise error
            
class IgorProcess(Thread):
    """
    Base class for all proceses
    """
    scope = None
    process_id = None
    output = None

    def __init__(self):
        Thread.__init__(self)