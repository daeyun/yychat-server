from twisted.test import proto_helpers
from twisted.trial import unittest
from time import strftime, gmtime
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot.yybot import YYBotFactory
from logger.sqlite_handler import SQLiteHandler
from server.request_handler import RequestHandlerFactory


class TestRequestHandler(unittest.TestCase):
    def setUp(self):
        self.db_manager = SQLiteHandler('test_db.sqlite3')

        self._network = 'localhost'
        self._channels = ['#test_channel']
        self._username = 'cat'

        self.bot_factory = YYBotFactory(
            self._network,
            self._channels,
            self._username,
        )

        self.request_handler_factory = RequestHandlerFactory()

        # IRC bot, SSL socket, SQLite handler should know each other
        self.bot_factory.add_request_handler(self.request_handler_factory)
        self.request_handler_factory.add_irc_bot(self.bot_factory)
        self.bot_factory.add_db_manager(self.db_manager)

        self.bot = self.bot_factory.buildProtocol(('127.0.0.1', 0))
        self.fake_bot_transport = proto_helpers.StringTransport()
        self.bot.makeConnection(self.fake_bot_transport)
        self.bot.signedOn()
        self.fake_bot_transport.clear()

        self.fake_receiver_transport = proto_helpers.StringTransport()
        self.request_handler = self.request_handler_factory.\
            buildProtocol(('127.0.0.1', 1))

        self.request_handler.makeConnection(self.fake_receiver_transport)
        self.fake_receiver_transport.clear()

        # send some requests first
        self.test_channel = '#test_channel2'
        request = {
            'type': 'send_message',
            'message': 'supgaiz',
            'target': self._channels[0],
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        request = {
            'type': 'join_channel',
            'channel': self.test_channel,
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        request = {
            'type': 'leave_channel',
            'channel': self.test_channel,
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        request = {
            'type': 'send_message',
            'message': 'hi friends',
            'target': self._channels[0],
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)
        self.fake_receiver_transport.clear()

    def tearDown(self):
        '''Delete sqlite file'''
        self.db_manager.remove()

    def test_get_logs(self):
        # client requests logs
        request = {
            'type': 'get_logs',
            'network': self._network,
            'target': self._channels[0],
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        # check logs sent
        response = {
            'type': 'get_logs',
            'content': [
                {
                    'type': 'status',
                    'date': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    'nick': self._username,
                    'target': self._channels[0],
                    'network': self._network,
                    'message': "has joined %s" % self._channels[0],
                },
                {
                    'type': 'msg',
                    'date': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    'nick': self._username,
                    'target': self._channels[0],
                    'network': self._network,
                    'message': 'supgaiz',
                },
                {
                    'type': 'msg',
                    'date': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    'nick': self._username,
                    'target': self._channels[0],
                    'network': self._network,
                    'message': 'hi friends',
                },
            ]
        }
        expected = json.dumps(response) + '\n'
        self.assertEqual(self.fake_receiver_transport.value(), expected)

    def test_get_join_leave_logs(self):
        # client requests logs
        request = {
            'type': 'get_logs',
            'network': self._network,
            'target': self.test_channel,
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        # check logs sent
        response = {
            'type': 'get_logs',
            'content': [
                {
                    'type': 'status',
                    'date': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    'nick': self._username,
                    'target': self.test_channel,
                    'network': self._network,
                    'message': "has joined %s" % self.test_channel,
                },
                {
                    'type': 'status',
                    'date': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    'nick': self._username,
                    'target': self.test_channel,
                    'network': self._network,
                    'message': "has left %s" % self.test_channel,
                },
            ]
        }
        expected = json.dumps(response) + '\n'
        self.assertEqual(self.fake_receiver_transport.value(), expected)
