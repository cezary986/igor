import sys 
sys.path.append('../../')

import unittest
from mock import IgorMock, ClientMock
from igor.core import Stream, ProcessOutput, handler_wrapper, flatten
import json
import time
import asyncio

class TestDictionaryFlatten(unittest.TestCase):

  def test_flatten(self):
    dictionary = {
      'a': {
        'b': 'c'
      },
      'd': 'e'
    }
    flattened = flatten(dictionary)
    values = list(flattened.values())
    keys = list(flattened.keys())
    if len(keys) != 2 or len(values) != 2:
      self.fail('Flattened dictionary should have two keys and two values')
    if keys[1] != 'a.b':
      self.fail('Flattened dictionary should have merged key names')
    if keys[0] != 'd' or values[0] != 'e':
      self.fail('Flattened dictionary should leave root level fields untouched')
    if values[1] != 'c':
      self.fail('Flattened fields should have correct values')

class TestStream(unittest.TestCase):

    def setUp(self):
      self.STREAM_ID = 'STREAM_ID'
      self.CLIENT_ID = "CLIENT_ID"

      self.igor_mock = IgorMock()
      self.client_mock = ClientMock(self.CLIENT_ID)

    def test_send(self):
      STREAM_DATA = {'test': 'test'}
      def mocked_send_message(client, serialized_message):
        try:
          serialized_message = json.loads(serialized_message)
        except Exception:
          self.fail('Stream data should be JSON serializable string')
        self.assertEqual(serialized_message['streamId'], self.STREAM_ID, 'Stream id should match')
        self.assertEqual(serialized_message['data'], STREAM_DATA, 'Stream data should match')
        self.assertEqual(client.id, self.CLIENT_ID, 'Clients id should match')

      self.igor_mock.server.send_message = mocked_send_message
      
      stream = Stream(self.igor_mock, self.client_mock, self.STREAM_ID, None)
      stream.send(STREAM_DATA)

    def test_send_error(self):
      STREAM_ERROR = 'ERROR'
      def mocked_send_message(client, serialized_message):
        try:
          serialized_message = json.loads(serialized_message)
        except Exception:
          self.fail('Stream data should be JSON serializable string')
        self.assertEqual(serialized_message['streamId'], self.STREAM_ID, 'Stream id should match')
        self.assertEqual(serialized_message['error'], STREAM_ERROR, 'Stream error should match')
        self.assertEqual(client.id, self.CLIENT_ID, 'Clients id should match')

      self.igor_mock.server.send_message = mocked_send_message
      
      stream = Stream(self.igor_mock, self.client_mock, self.STREAM_ID, None)
      stream.send_error(STREAM_ERROR)

    def test_close(self):
      did_call_callback = {'value': False}
      def mocked_send_message(client, serialized_message):
        try:
          serialized_message = json.loads(serialized_message)
        except Exception:
          self.fail('Stream data should be JSON serializable string')
        close = serialized_message.get('close', None)
        if close == None:
           self.fail('Stream closing message should have "close" field')
        self.assertEqual(serialized_message['streamId'], self.STREAM_ID, 'Stream id should match')
        self.assertEqual(client.id, self.CLIENT_ID, 'Clients id should match')
        self.assertEqual(close, True, '"close" should have value True')
      
      def mocked_close_callback(igor_server, stream_id):
        did_call_callback['value'] = True
        self.assertEqual(stream_id, self.STREAM_ID, 'Stream id should match')
        self.assertEqual(igor_server, self.igor_mock, 'Igor server instance should be passed')

      self.igor_mock.server.send_message = mocked_send_message
      stream = Stream(self.igor_mock, self.client_mock, self.STREAM_ID, mocked_close_callback)
      stream.close()
      time.sleep(0.2)
      self.assertEqual(did_call_callback['value'], True, 'Stream should call "on_close_callback"')

class TestProcessOutput(unittest.TestCase):

    def setUp(self):
      self.STREAM_ID = 'STREAM_ID'
      self.PROCESS_ID = "PROCESS_ID"
      self.CLIENT_ID = "CLIENT_ID"
      self.ACTION = "ACTION"

      self.client_mock = ClientMock(self.CLIENT_ID)
      self.igor_mock = IgorMock()
      self.igor_mock.clients = {
        'CLIENT_ID': self.client_mock
      }

    def test_send_to_valid_client(self):
      STREAM_DATA = {'test': 'test'}
      def mocked_send_message(client, serialized_message):
        try:
          serialized_message = json.loads(serialized_message)
        except Exception:
          self.fail('Stream data should be JSON serializable string')
        self.assertEqual(serialized_message['streamId'], self.PROCESS_ID, 'Stream id should match process id')
        self.assertEqual(serialized_message['data'], STREAM_DATA, 'Stream data should match')
        self.assertEqual(client, self.client_mock, 'Clients should match')

      self.igor_mock.server.send_message = mocked_send_message
      
      output = ProcessOutput(self.PROCESS_ID, self.igor_mock, None)
      output.send(self.ACTION, STREAM_DATA, client_id=self.CLIENT_ID)

    def test_send_to_nonexisting_client(self):
      output = ProcessOutput(self.PROCESS_ID, self.igor_mock, None)
      self.assertRaises(
        Exception,
        'Sending message to invalid client id should raise an Exception',
        output.send, 
        self.ACTION, 
        None, 
        client_id='NONEXISING_CLIENT'
      )
    
    def test_send_to_all(self):
      was_send_to_all_called = {'value': False}
      STREAM_DATA = {'test': 'test'}
      def mocked_send_message_to_all(serialized_message):
        was_send_to_all_called['value'] = True
        try:
          serialized_message = json.loads(serialized_message)
        except Exception:
          self.fail('Stream data should be JSON serializable string')
        self.assertEqual(serialized_message['streamId'], self.PROCESS_ID, 'Stream id should match process id')
        self.assertEqual(serialized_message['data'], STREAM_DATA, 'Stream data should match')

      self.igor_mock.server.send_message_to_all = mocked_send_message_to_all
      
      output = ProcessOutput(self.PROCESS_ID, self.igor_mock, None)
      output.send(self.ACTION, STREAM_DATA)
      time.sleep(0.2)
      self.assertEqual(was_send_to_all_called['value'], True, 'Should call "send_message_to_all" on server')

    def test_send_error(self):
      STREAM_ERROR = 'STREAM_ERROR'
      def mocked_send_message(client, serialized_message):
        try:
          serialized_message = json.loads(serialized_message)
        except Exception:
          self.fail('Stream data should be JSON serializable string')
        self.assertEqual(serialized_message['streamId'], self.PROCESS_ID, 'Stream id should match process id')
        self.assertEqual(serialized_message['error'], STREAM_ERROR, 'Stream error should match')
        self.assertEqual(client, self.client_mock, 'Clients should match')

      self.igor_mock.server.send_message = mocked_send_message
      
      output = ProcessOutput(self.PROCESS_ID, self.igor_mock, None)
      output.send_error(STREAM_ERROR, client_id=self.CLIENT_ID)

    def test_finish(self):
      did_call_callback = {'value': False}
      def mocked_send_message_to_all(serialized_message):
        try:
          serialized_message = json.loads(serialized_message)
        except Exception:
          self.fail('Stream data should be JSON serializable string')
        close = serialized_message.get('close', None)
        if close == None:
           self.fail('Stream closing message should have "close" field')
        self.assertEqual(serialized_message['streamId'], self.PROCESS_ID, 'Stream id should match')
        self.assertEqual(close, True, '"close" should have value True')
      
      def mocked_finish_callback(igor_server, stream_id):
        did_call_callback['value'] = True
        self.assertEqual(stream_id, self.PROCESS_ID, 'Stream id should match')
        self.assertEqual(igor_server, self.igor_mock, 'Igor server instance should be passed')

      self.igor_mock.server.send_message_to_all = mocked_send_message_to_all
      
      output = ProcessOutput(self.PROCESS_ID, self.igor_mock, mocked_finish_callback)
      output.finish()
      self.assertEqual(output.closed, True, 'Ouput "closed" field value should be True')
      time.sleep(0.2)
      self.assertEqual(did_call_callback['value'], True, 'Should call "on_finish_callback"')

class TestHandlerWrapper(unittest.TestCase):

  def setUp(self):
    self.STREAM_ID = 'STREAM_ID'
    self.igor_mock = IgorMock()
    def mock_send_message(client, serialized_message):
      pass
    self.igor_mock.server.send_message = mock_send_message
    self.CLIENT_ID = "CLIENT_ID"
    self.client_mock = ClientMock(self.CLIENT_ID)
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

  def test_if_closes_stream(self):
    did_call_callback = {'value': False}
    did_call_function = {'value': False}
    STREAM_DATA = {'test': 'test'}
    def mocked_close_callback(igor_server, stream_id):
      self.assertEqual(stream_id, self.STREAM_ID, 'Stream id should match')
      self.assertEqual(igor_server, self.igor_mock, 'Igor server instance should be passed')
      did_call_callback['value'] = True
    
    stream = Stream(self.igor_mock, self.client_mock, self.STREAM_ID, mocked_close_callback)

    def function(stream, data, **kwargs):
      did_call_function['value'] = True
      self.assertEqual(stream.stream_id, self.STREAM_ID, 'Stream id should match')
      self.assertEqual(data, STREAM_DATA, 'Stream data should match')

    self.loop.run_until_complete(handler_wrapper(function, stream, STREAM_DATA, {}, {}))
    time.sleep(0.1)
    self.assertEqual(did_call_function['value'], True, 'Should call function')
    self.assertEqual(did_call_callback['value'], True, 'Should close stream after handler function finish')
    

if __name__ == '__main__':
  unittest.main()