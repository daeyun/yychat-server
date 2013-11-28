from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
import random


class RequestHandler(LineReceiver):
    def __init__(self, users):
        self.users = users
        self.delimiter = "\n"

    def connectionMade(self):
        log.msg("Client joined!")
        self.name = random.random()
        self.users[self.name] = self

    def connectionLost(self, reason):
        log.msg("Client left!")
        if self.name in self.users:
            del self.users[self.name]

    def lineReceived(self, line):
        log.msg("Client sent data: ", line)
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

    def get_message(self, nick, userhost, channel, message):
        for name, protocol in self.users.iteritems():
            protocol.sendLine("NEW_MESSAGE " + channel + " " + nick + " " + userhost + " " + message)

    def notify_user_mode_change(self, sender_nick, channel, mode, nick):
        for name, protocol in self.users.iteritems():
            protocol.sendLine("USER_MODE_CHANGE " + sender_nick + " " + channel + "" + mode + " " + nick)
