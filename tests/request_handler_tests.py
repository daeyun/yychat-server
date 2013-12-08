from twisted.test import proto_helpers
from twisted.trial import unittest
from hashlib import md5
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

    def tearDown(self):
        '''Delete sqlite file'''
        self.db_manager.remove()

    def test_list_channels(self):
        request = {
            'type': 'list_channels',
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        response = {
            'type': 'list_channels',
            'content': self._channels,
        }
        expected = json.dumps(response) + '\n'
        self.assertEqual(self.fake_receiver_transport.value(), expected)

    def test_join_channel(self):
        self.assertEqual(len(self.bot_factory.channels), 1)

        request = {
            'type': 'join_channel',
            'channel': '#test_channel2',
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        # manually call the callback to simulate joining a channel
        self.bot.joined('#test_channel2')

        response = {
            'type': 'list_channels',
            'content': self._channels,
        }
        expected = json.dumps(response) + '\n'
        self.assertEqual(self.fake_receiver_transport.value(), expected)
        self.assertEqual(len(self.bot_factory.channels), 2)

    def test_get_nickname(self):
        self.assertEqual(len(self.bot_factory.channels), 1)

        request = {
            'type': 'get_nickname',
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        response = {
            'type': 'get_nickname',
            'content': self._username,
        }
        expected = json.dumps(response) + '\n'
        self.assertEqual(self.fake_receiver_transport.value(), expected)

    def test_send_message(self):
        request = {
            'type': 'send_message',
            'message': 'supgaiz',
            'target': self._channels[0],
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        response = {
            'hash': md5(request_str).hexdigest(),
        }
        expected = json.dumps(response)
        actual = self.fake_receiver_transport.value().strip()
        self.assertEqual(actual, expected)

        expected = "PRIVMSG #test_channel :supgaiz"
        actual = self.fake_bot_transport.value().strip()
        self.assertEqual(actual, expected)

    def test_leave_channel(self):
        self.assertEqual(len(self.bot_factory.channels), 1)

        request = {
            'type': 'leave_channel',
            'channel': '#test_channel',
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        # manually call the callback to simulate leaving a channel
        self.bot.left('#test_channel')

        # left() sends back a list of channels
        response = {
            'type': 'list_channels',
            'content': []
        }
        expected = json.dumps(response) + '\n'
        self.assertEqual(self.fake_receiver_transport.value(), expected)
        self.assertEqual(len(self.bot_factory.channels), 0)

    def test_leave_channel_invalid(self):
        self.assertEqual(len(self.bot_factory.channels), 1)

        # trying to leave a channel without joining it first
        request = {
            'type': 'leave_channel',
            'channel': '#random_channel_42',
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        # nothing should happen
        expected = ''
        self.assertEqual(self.fake_receiver_transport.value(), expected)
        self.assertEqual(len(self.bot_factory.channels), 1)
