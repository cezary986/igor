import sys
sys.path.append('../../')
import asyncio
import time
from mock import ClientMock
from igor.core import IgorProcess, Stream
from igor.server import IgorServer
import unittest
from unittest.mock import MagicMock, Mock
import json
import subprocess

class TestServer(unittest.TestCase):

    def setUp(self):
        self.STREAM_ID = 'STREAM_ID'
        self.CLIENT_ID = 'CLIENT_ID'
        self.client = ClientMock(self.CLIENT_ID)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_register_new_client(self):
        igor = IgorServer(api={})
        igor._IgorServer__register_new_client(self.client.__dict__, igor)
        self.assertTrue(igor.clients.get(self.CLIENT_ID, None)
                        != None, 'Should add new client to dictionary')
        self.assertEqual(
            igor.clients[self.CLIENT_ID], self.client.__dict__, 'Client object should match')
        self.assertTrue(igor.sessions.get(self.CLIENT_ID, None)
                        != None, 'New session object should be created')

    def test_adding_multiple_clients_with_same_id(self):
        igor = IgorServer(api={})
        igor._IgorServer__register_new_client(self.client.__dict__, igor)
        self.assertRaises(
            Exception,
            'Should not be able to add multiple clients with same id',
            igor._IgorServer__register_new_client,
            self.client.__dict__,
            igor
        )

    def test_unregister_new_client(self):
        igor = IgorServer(api={})
        igor._IgorServer__register_new_client(self.client.__dict__, igor)
        igor.clients[self.CLIENT_ID] = self.client.__dict__
        igor.session_delete_timeout = 0.1
        igor._IgorServer__unregister_client(self.client.__dict__, igor)
        self.assertTrue(igor.clients.get(self.CLIENT_ID, None)
                        == None, 'Should remove client from dictionary')
        self.assertTrue(igor.sessions.get(self.CLIENT_ID, None) !=
                        None, "Shouldn't remove client's session immediately")
        time.sleep(0.2)
        self.assertTrue(igor.sessions.get(self.CLIENT_ID, None)
                        == None, "Should remove client's session after timeout")

    def test_add_new_stream(self):
        igor = IgorServer(api={})
        stream = igor._IgorServer__add_new_stream(
            self.STREAM_ID, self.client.__dict__)
        self.assertTrue(igor.streams.get(self.STREAM_ID, None)
                        != None, 'Should add new stream to dictionary')
        self.assertEqual(stream.stream_id, self.STREAM_ID,
                         'Should return new Stream instance')

    def test_remove_stream(self):
        igor = IgorServer(api={})
        stream = igor._IgorServer__add_new_stream(
            self.STREAM_ID, self.client.__dict__)
        stream = igor._IgorServer__remove_stream(igor, self.STREAM_ID)
        self.assertTrue(igor.streams.get(self.STREAM_ID, None)
                        == None, 'Should remove stream from dictionary')

    def test_add_process(self):
        PROCESS_ID = 'PROCESS_ID'
        was_process_running = {'value': False}
        igor = IgorServer(api={})

        class TestProcess(IgorProcess):

            def __init__(self, test_class):
                IgorProcess.__init__(self)
                self.test_class = test_class

            def run(self):
                was_process_running['value'] = True
                self.test_class.assertTrue(self.__dict__.get(
                    'scope', None) != None, 'Scope variable should be injected to process')
                self.test_class.assertTrue(self.__dict__.get(
                    'process_id', None) == 'PROCESS_ID', 'Process id should be injected to process')
                self.test_class.assertTrue(self.__dict__.get(
                    'output', None) != None, 'Output object should be injected to process')

        igor.add_process(PROCESS_ID, TestProcess(self))
        igor.server = MagicMock()
        igor.server.run_forever = Mock(return_value=None)
        igor.run_forever()
        self.assertTrue(
            was_process_running['value'], 'Process should have run')
        self.assertTrue(igor.processes.get(PROCESS_ID, None) !=
                        None, 'Process should be added to dictionary')

    def test_remove_process(self):
        PROCESS_ID = 'PROCESS_ID'
        igor_server = IgorServer(api={})
        thread_mock = MagicMock()
        thread_mock.kill = Mock()
        igor_server.processes[PROCESS_ID] = {
            'thread': thread_mock, 'output': None}
        igor_server._IgorServer__remove_process(igor_server, PROCESS_ID)
        self.assertEqual(thread_mock.kill.call_count, 1, 'Thread kill method should be called once')
        self.assertTrue(igor_server.processes.get(PROCESS_ID, None)
                        == None, 'Should remove process from dictionary')

    def test_main_handler(self):
        ACTION_ID = 'ACTION_ID'
        STREAM_ID = 'STREAM_ID'
        CLIENT_ID = 'CLIENT_ID'
        STREAM_DATA = 'STREAM_DATA'
        MOCKED_SCOPE = 'MOCKED_SCOPE'
        MOCKED_SESSION = 'MOCKED_SESSION'
        mock = Mock()
        def mocked_handler(out, data, **kwargs):
          self.assertIsInstance(out, Stream, 'First parameter of handler should be output Stream object')
          self.assertEqual(data, STREAM_DATA, 'Second parameter of handler should be message data')
          self.assertTrue(kwargs.get('session', None) != None, 'Handlers kwargs should contain session object')
          self.assertEqual(kwargs.get('session', None), MOCKED_SESSION, 'Session object should be clients session object')
          self.assertTrue(kwargs.get('scope', None) != None, 'Handlers kwargs should contain scope object')
          self.assertEqual(kwargs.get('scope', None), MOCKED_SCOPE, 'Scope object should match')
          mock()
        mocked_handler
        igor_server = IgorServer(api={'ACTION_ID': mocked_handler})
        igor_server.scope = MOCKED_SCOPE
        igor_server.sessions[CLIENT_ID] = MOCKED_SESSION
        igor_server.server = MagicMock()
        igor_server.server.send_message = Mock()
        message = {
          'streamId': STREAM_ID,
          'data': STREAM_DATA,
          'action': ACTION_ID
        }
        message = json.dumps(message)
        igor_server._IgorServer__main_handler({'id': CLIENT_ID}, MagicMock(), message)
        self.assertEqual(mock.call_count, 1, 'Handler function should be called once')

    def test_main_handler_for_nonexisting_action(self):
        ACTION_ID = 'NONEXISTING_ACTION_ID'
        STREAM_ID = 'STREAM_ID'
        STREAM_DATA = 'STREAM_DATA'
        igor_server = IgorServer(api={})
        igor_server._IgorServer__send_erorr = Mock()
        message = {
          'streamId': STREAM_ID,
          'data': STREAM_DATA,
          'action': ACTION_ID
        }
        message = json.dumps(message)
        igor_server._IgorServer__main_handler(MagicMock(), MagicMock(), message)
        self.assertEqual(igor_server._IgorServer__send_erorr.call_count, 1, 'Should send error if there is no handler for action')

    def test_main_handler_for_message_without_specified_action(self):
        STREAM_ID = 'STREAM_ID'
        STREAM_DATA = 'STREAM_DATA'
        igor_server = IgorServer(api={})
        igor_server._IgorServer__send_erorr = Mock()
        message = {
          'streamId': STREAM_ID,
          'data': STREAM_DATA,
        }
        message = json.dumps(message)
        igor_server._IgorServer__main_handler(MagicMock(), MagicMock(), message)
        self.assertEqual(igor_server._IgorServer__send_erorr.call_count, 1, 'Should send error if there is no action specified in message')

    def test_binding_to_ui_process(self):
        igor_server = IgorServer(api={})
        igor_server._IgorServer__send_erorr = Mock()
        igor_server._IgorServer__kill = Mock()
        mock_process = subprocess.Popen('ping 127.0.0.1')
        igor_server.bind_with_ui_process(mock_process)
        time.sleep(5)
        mock_process.kill()
        self.assertEqual(igor_server._IgorServer__kill.call_count, 1, 'Server should kill itself after ui process')

if __name__ == '__main__':
    unittest.main()
