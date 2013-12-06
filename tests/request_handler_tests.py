from twisted.test import proto_helpers
from twisted.trial import unittest
from hashlib import md5
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot.yybot import YYBotFactory
from server.request_handler import RequestHandlerFactory


class TestRequestHandler(unittest.TestCase):
    _channels = ['#test_channel']
    _username = 'cat'

    def setUp(self):
        bot_factory = YYBotFactory(self._channels, self._username)

        self.bot = bot_factory.buildProtocol(('127.0.0.1', 0))
        self.fake_bot_transport = proto_helpers.StringTransport()
        self.bot.makeConnection(self.fake_bot_transport)
        self.bot.signedOn()
        self.bot.joined(self._channels)
        self.fake_bot_transport.clear()

        request_handler_factory = RequestHandlerFactory()

        self.request_handler = request_handler_factory.buildProtocol(('127.0.0.1', 1))
        self.fake_receiver_transport = proto_helpers.StringTransport()
        request_handler_factory.add_irc_bot(bot_factory)

        bot_factory.add_request_handler(request_handler_factory)
        self.request_handler.makeConnection(self.fake_receiver_transport)
        self.fake_receiver_transport.clear()

    def test_list_channels(self):
        request = {
            "type": "list_channels",
        }
        request_str = json.dumps(request)
        self.request_handler.lineReceived(request_str)

        response = {
            "content": self._channels,
            "hash": md5(request_str).hexdigest(),
        }

        expected = json.dumps(response) + '\n'  # ["#test_channel"]\n
        self.assertEqual(expected, self.fake_receiver_transport.value())
