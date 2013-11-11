from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
import random


class RequestHandler(LineReceiver):
    def __init__(self, users):
        self.users = users

    def connectionMade(self):
        name = random.random()
        self.users[name] = self

    def connectionLost(self, reason):
        if self.name in self.users:
            del self.users[self.name]

    def lineReceived(self, line):
        self.factory.irc_bot.send_message("#yychat", line)

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

    def get_message(self, user, channel, message):
        for name, protocol in self.users.iteritems():
            protocol.sendLine(channel + " " + user + " " + message)
