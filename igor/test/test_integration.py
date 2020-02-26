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
import websocket

import os

try:
    igor_process = subprocess.Popen('START ' + os.getcwd() + '\..\..\env\Scripts\python.exe server_instance.py', shell=True)
except Exception:
    print('Unable to start igor server instance. Check if the port is not already in use')

class TestServerIntegration(unittest.TestCase):
        
    def test_calling_handler(self):
        ws = websocket.WebSocket()
        try:
          ws.connect("ws://localhost:5678")
        except error:
          self.fail('Should be able to connect to server. Check if port is not already in use')
        ws.send(json.dumps({
          'streamId': 'test_calling_handler',
          'data': "DATA",
          'action': 'echo'
        }))
        result =  ws.recv()
        try:
          result = json.loads(result)
        except error:
          self.fail('Message from server should be json serializable')
        print(result)
        self.assertTrue(result.get('streamId', None) != None, 'Message should contain streamId field')
        self.assertTrue(result.get('data', None) != None, 'Message should contain data field')
        self.assertEqual(result['streamId'], 'test_calling_handler', 'Stream id should match the one send by the client')
        self.assertEqual(result['data'], 'DATA', 'Server should receive data from client')
        
    def test_process(self):
        ws = websocket.WebSocket()
        try:
          ws.connect("ws://localhost:5678")
        except Exception:
          self.fail('Should be able to connect to server. Check if port is not already in use')
        result =  ws.recv()
        try:
          result = json.loads(result)
        except Exception:
          self.fail('Message from server should be json serializable')
        print(result)
        self.assertTrue(result.get('streamId', None) != None, 'Message should contain streamId field')
        self.assertTrue(result.get('data', None) != None, 'Message should contain data field')
        self.assertTrue(result.get('action', None) != None, 'Message should contain action field')
        self.assertEqual(result['streamId'], 'test_process', 'Stream id should match name of the process')
        self.assertEqual(result['action'], 'tick', 'Client should receive data from process')
        self.assertEqual(result['data'], 'tack', 'Client should receive data from process')
    
    def test_introduce_self(self):
        CLIENT_ID = 'CLIENT_1'
        ws = websocket.WebSocket()
        try:
          ws.connect("ws://localhost:5678")
        except Exception:
          self.fail('Should be able to connect to server. Check if port is not already in use')
        ws.send(json.dumps({
          'streamId': 'introduce_self_stream_id',
          'data': {'client_id': CLIENT_ID },
          'action': 'introduce_self'
        }))
        time.sleep(0.5)
        received_message = None
        for i in range(5):
            result =  ws.recv()
            if json.loads(result)['data'] != 'tack':
              received_message = json.loads(result)
        if received_message == None:
          self.fail('Introduce self should change client id so process could send only to him')
        self.assertTrue(received_message.get('streamId', None) != None, 'Message should contain streamId field')
        self.assertTrue(received_message.get('data', None) != None, 'Message should contain data field')
        self.assertTrue(received_message.get('action', None) != None, 'Message should contain action field')
        self.assertEqual(received_message['streamId'], 'test_process', 'Stream id should match name of the process')
        self.assertEqual(received_message['action'], 'tick', 'Client should receive data from process')
        self.assertEqual(received_message['data'], 'special_for_CLIENT_1', 'Client should receive data from process')
    
    def test_sending_to_specified_client(self):
        ws = websocket.WebSocket()
        try:
          ws.connect("ws://localhost:5678")
        except Exception:
          self.fail('Should be able to connect to server. Check if port is not already in use')
        received_message = None
        for i in range(5):
            result =  ws.recv()
            if json.loads(result)['data'] != 'tack':
              received_message = json.loads(result)
        if received_message != None:
          self.fail('Process should be able to send messages only to specified client')

if __name__ == '__main__':
    time.sleep(2)
    unittest.main()
    igor_process.kill()
