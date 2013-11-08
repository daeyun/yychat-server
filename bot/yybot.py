from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import time


class YYBot(irc.IRCClient):
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        log.msg("[connected at %s]" % time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        log.msg("[disconnected at %s]" % time.asctime(time.localtime(time.time())))

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        log.msg("[signedOn at %s]" % time.asctime(time.localtime(time.time())))

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        log.msg("[joined %s]" % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        log.msg(">> <%s> %s %s" % (user, channel, msg))

        user = user.split('!', 1)[0]
        log.msg("<%s> %s" % (user, msg))

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "Received a privte message"
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname):
            msg = "%s: =^_^=" % user
            self.msg(channel, msg)
            log.msg("<%s> %s" % (self.nickname, msg))

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        log.msg("* %s %s" % (user, msg))

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        log.msg("%s is now known as %s" % (old_nick, new_nick))

    # Override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """ Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration. """
        return nickname + '^'


class YYBotFactory(protocol.ClientFactory):
    """A new protocol instance will be created each time we connect to
    the server. """

    def __init__(self, channel, nickname):
        self.channel = channel
        self.nickname = nickname

    def buildProtocol(self, addr):
        p = YYBot()
        p.factory = self
        p.nickname = self.nickname
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        """Connection Failed."""
        reactor.stop()
