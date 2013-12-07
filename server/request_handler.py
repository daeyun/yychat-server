from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from hashlib import md5
import random
import json


class RequestHandler(LineReceiver):
    def __init__(self, users):
        self.users = users
        self.delimiter = "\n"

    def connectionMade(self):
        self.name = random.random()
        log.msg("Client %s joined!" % self.name)
        self.users[self.name] = self

    def connectionLost(self, reason):
        log.msg("Client %s left!" % self.name)
        if self.name in self.users:
            del self.users[self.name]

    def lineReceived(self, line):
        log.msg("Client %s sent data: " % self.name, line)

        request = json.loads(line.strip())
        request_type = request['type'].encode('ascii', 'ignore').lower()

        {
            'send_message': self.handle_send_message,
            'list_channels': self.handle_list_channels,
            'join_channel': self.handle_join_channel,
            'get_nickname': self.handle_get_nickname,
        }[request_type](request, md5(line).hexdigest())

    def handle_send_message(self, request, hash):
        """Send a message to the IRC server and send a confirmation message
        to the client containing the hash of the request string."""
        target = request['target'].encode('ascii', 'ignore')
        message = request['message'].encode('ascii', 'ignore')

        self.factory.irc_bot.send_message(target, message)

        response = {
            'hash': hash,
        }
        self.sendLine(json.dumps(response))

    def handle_list_channels(self, request, hash):
        """Respond with the list of currently joined channels."""
        response = {
            'type': 'list_channels',
            'content': self.factory.irc_bot.channels,
            'hash': hash,
        }
        self.sendLine(json.dumps(response))

    def handle_join_channel(self, request, hash):
        channel = request['channel'].encode('ascii', 'ignore')
        self.factory.irc_bot.join_channel(channel)

    def handle_get_nickname(self, request, hash):
        response = {
            'type': 'get_nickname',
            'content': self.factory.irc_bot.nickname,
            'hash': hash,
        }
        self.sendLine(json.dumps(response))


class RequestHandlerFactory(Factory):
    def __init__(self):
        self.users = {}

    def add_irc_bot(self, irc_bot):
        self.irc_bot = irc_bot

    def buildProtocol(self, addr):
        self.protocol = RequestHandler(self.users)
        self.protocol.factory = self
        return self.protocol

    def get_message(self, nick, userhost, channel, message):
        for name, protocol in self.users.iteritems():
            response = {
                'type': 'new_message',
                'channel': channel,
                'sender_nick': nick,
                'sender_hostmask': userhost,
                'message': message,
            }
            protocol.sendLine(json.dumps(response))

    def list_channels(self):
        for name, protocol in self.users.iteritems():
            response = {
                'type': 'list_channels',
                'content': self.irc_bot.channels,
            }
            protocol.sendLine(json.dumps(response))

    def notify_user_mode_change(self, sender_nick, channel, mode, nick):
        for name, protocol in self.users.iteritems():
            response = {
                'type': 'user_mode_change',
                'channel': channel,
                'sender_nick': sender_nick,
                'nick': nick,
                'mode': mode,
            }
            protocol.sendLine(json.dumps(response))
