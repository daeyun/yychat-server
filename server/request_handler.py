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
        request_type = request['type'].lower()

        {
            'send_message': self.handle_send_message,
            'list_channels': self.handle_list_channels
        }[request_type](request, md5(line).hexdigest())

    def handle_send_message(self, request, hash):
        """Send a message to the IRC server and send a confirmation message
        to the client containing the hash of the request string."""
        target = request['target'].encode('ascii', 'ignore')
        message = request['message'].encode('ascii', 'ignore')

        self.factory.irc_bot.send_message(target, message)

        response = {
            "hash": hash,
        }
        self.sendLine(json.dumps(response))

    def handle_list_channels(self, request, hash):
        """Respond with the list of currently joined channels."""
        response = {
            "content": self.factory.irc_bot.channels,
            "hash": hash,
        }
        self.sendLine(json.dumps(response))

    #def handle_CHAT(self, message):
        #message = "<%s> %s" % (self.name, message)
        #for name, protocol in self.users.iteritems():
            #protocol.sendLine(message)


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
            protocol.sendLine("NEW_MESSAGE " + channel + " " + nick + " " + userhost + " " + message)

    def notify_user_mode_change(self, sender_nick, channel, mode, nick):
        for name, protocol in self.users.iteritems():
            protocol.sendLine("USER_MODE_CHANGE " + sender_nick + " " + channel + "" + mode + " " + nick)
