import asyncio
from websocket_server import WebsocketServer
import json
import logging
from threading import Timer
from igor.file_server import run_file_server
import time
import threading
import _thread 
from igor.core import Stream, handler_wrapper, ProcessOutput

CONFIG = {
    'port': 5678,
    'host': 'localhost',
    'file_server': False,
    'file_server_config': {
        'enable': False,
        'port': 8080,
        'root_directory': None  # default is system root
    },
    'logging': {
        'level': logging.ERROR,
        'file_name': 'igor_error.log'
    },
}


class IgorServer:

    def __init__(self, api=None, config=CONFIG):
        """
        :param api: api dictionary containing handler functions
        :param config: config object
        """
        if not isinstance(api, dict):
            raise Exception("API config object must be dictionary object")
        else:
            self.paths = api

        self.config = config
        self.streams = {}
        self.clients = {}
        self.timeouts = {}
        self.sessions = {}
        self.processes = {}
        self.scope = {}
        self.loop = asyncio.get_event_loop()

        self.server = WebsocketServer(
            config['port'],
            host=config['host'],
            loglevel=config['logging']['level'])
        self.server.set_fn_new_client(self.__register_new_client)
        self.server.set_fn_client_left(self.__unregister_client)
        self.server.set_fn_message_received(self.__main_handler)

        self.session_delete_timeout = 10.0

        self.__configure(config)

    def __configure(self, config):
        if config['file_server_config']['enable']:
            run_file_server(
                config['file_server_config']['port'],
                config['file_server_config']['root_directory'])
        if config['logging']['file_name']:
            logging.basicConfig(filename=config['logging']['file_name'])
        logging.basicConfig(level=config['logging']['level'])

    def run_forever(self):
        logging.debug("Starting server")
        for process_id, process in self.processes.items():
            thread = process['thread']
            thread.daemon = True
            print('Starting thread')
            thread.start()
        self.server.run_forever()

    def __register_new_client(self, client, server):
        if client.get('id', None) is None:
            raise Exception('Trying to register client without id')
        if self.clients.get(client['id'], None) is not None:
            raise Exception('Client with id: "' + client['id'] + '" already connected')
        logging.debug('New client: "' + str(client['id']) + '" registered')
        self.clients[client['id']] = client
        self.sessions[client['id']] = {}

    def __unregister_client(self, client, server):
        logging.debug('Client: "' + str(client['id']) + '" unregistered')
        del self.clients[client['id']]

        def delete_session(client_id, igor_server):
            _client = igor_server.clients.get(client_id, None)
            if _client is None:
                del self.sessions[client_id]
        timeout = Timer(self.session_delete_timeout, delete_session, [client['id'], self])
        self.timeouts[client['id']] = timeout
        timeout.start()

    def __add_new_stream(self, stream_id, client):
        logging.debug('Stream added')
        stream = Stream(self, client, stream_id, self.__remove_stream)
        self.streams[stream_id] = stream
        return stream

    def __remove_stream(self, real_self, stream_id):
        logging.debug('Stream removed')
        del real_self.streams[stream_id]

    def add_process(self, process_id, thread):
        """
        Adds new process to server - it won't be started immediately, to start it run: run_forever method

        :process_id: id of the process
        :thread: thread object of the process
        """
        output = ProcessOutput(process_id, self, self._IgorServer__remove_process)
        thread.process_id = process_id
        thread.output = output
        thread.scope = self.scope
        thread.sessions = self.sessions
        self.processes[process_id] = {'thread': thread, 'output': output}

    def __remove_process(self, real_self, process_id):
        logging.debug('Process with id: "' + process_id + '" finished and is removed')
        real_self.processes[process_id]['thread'].kill()
        del real_self.processes[process_id]

    def __send_erorr(self, client, message, code=500):
        logging.error(message)
        self.server.send_message(client, json.dumps({'error': message, 'code': code}))

    def __introduce_self(self, client, stream_data):
        client_id = stream_data.get('client_id', None)
        if client_id is None:
            self.__send_erorr(client, 'No client_id for introduce_self action', code=400)
            return
        else:
            client_session = self.sessions.get(client_id, None)
            if client_session is not None:
                timeout = self.timeouts.get(client['id'], None)
                if timeout is not None:
                    timeout.cancel()
            else:
                client_session = self.sessions[client['id']]
            del self.sessions[client['id']]
            del self.clients[client['id']]
            self.clients[stream_data['client_id']] = client
            self.sessions[stream_data['client_id']] = client_session
            client['id'] = stream_data['client_id']

    def __main_handler(self, client, server, message):
        try:
            message = json.loads(message)
            stream_id = message.get('streamId', None)

            if stream_id is None:
                self.__send_erorr(client, 'No streamId specified', code=400)
            else:
                stream_data = message.get('data', None)
                action = message.get('action', None)
                if action is None:
                    self.__send_erorr(client, 'No action specified', code=400)
                    return
                if action == 'introduce_self':
                    self.__introduce_self(client, stream_data)
                    return
                handler_function = self.paths.get(action, None)
                if handler_function is None:
                    self.__send_erorr(client, 'No handler for action: "' + action + '"', code=400)
                    return
                stream = self.streams.get(stream_id, None)
                if stream is None:
                    stream = self.__add_new_stream(stream_id, client)
                session = self.sessions.get(client['id'], None)
                print(session)

                self.loop.run_until_complete(handler_wrapper(handler_function, stream, stream_data, session, self.scope))
        except SystemExit:
            logging.debug('System exit exception shutting down')
            _thread.interrupt_main()
        except Exception as error:
            logging.error(str(error))
            self.__send_erorr(client, 'Undefined error occured while handling message', code=503)
            raise error
