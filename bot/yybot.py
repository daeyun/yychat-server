from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.internet import defer

import time


class YYBot(irc.IRCClient):
    def __init__(self):
        self._namescallback = {}

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

        datetime = time.asctime(time.localtime(time.time()))
        log.msg("[connected at %s]" % datetime)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

        datetime = time.asctime(time.localtime(time.time()))
        log.msg("[disconnected at %s]" % datetime)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""

        for channel in self.factory.channels:
            self.factory.join_channel(channel)
        log.msg("[signedOn at %s]" % time.asctime(time.localtime(time.time())))

    def joined(self, channel):
        """This will get called when the bot joins a channel."""
        log.msg("[joined %s]" % channel)

        if channel not in self.factory.channels:
            self.factory.channels.append(channel)
            self.factory.request_handler.list_channels()

        def got_names(nicklist):
            self.names("channel").addCallback()

    def left(self, channel):
        """This will get called when the bot leaves a channel."""
        log.msg("[left %s]" % channel)

        if channel in self.factory.channels:
            self.factory.channels.remove(channel)
            self.factory.request_handler.list_channels()

    def privmsg(self, hostmask, channel, msg):
        """This will get called when the bot receives a message."""
        sender_nick = hostmask.split('!', 1)[0]
        userhost = hostmask.split('!', 1)[1]
        log.msg("<%s> %s" % (hostmask, msg))

        self.factory.request_handler.get_message(sender_nick, userhost,
                                                 channel, msg)

        # Check to see if they're sending me a private message
        #if channel == self.nickname:
            #msg = "Received a privte message"
            #self.msg(user, msg)
            #return

        # Otherwise check to see if it is a message directed at me
        #if msg.startswith(self.nickname):
            #msg = "%s: =^_^=" % user
            #self.msg(channel, msg)
            #log.msg("<%s> %s" % (self.nickname, msg))

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        log.msg("* %s %s" % (user, msg))

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        log.msg("%s is now known as %s" % (old_nick, new_nick))

    def irc_MODE(self, hostmask, params):
        """Parse the server message when one or more modes are changed."""
        sender_nick = hostmask.split('!', 1)[0]
        channel = params[0]
        mode = params[1]  # "+v", for example

        if (len(params) == 3):
            nick = params[2]
            self.factory.request_handler.\
                notify_user_mode_change(sender_nick, channel, mode, nick)

    def alterCollidedNick(self, nickname):
        """ Determine how a nickname is changed on collisions. The default
        method appends an underscore. """
        return nickname + '^'

    def names(self, channel):
        channel = channel.lower()
        d = defer.Deferred()
        if channel not in self._namescallback:
            self._namescallback[channel] = ([], [])

        self._namescallback[channel][0].append(d)
        self.sendLine("NAMES %s" % channel)
        return d

    def irc_RPL_NAMREPLY(self, prefix, params):
        channel = params[2].lower()
        nicklist = params[3].split(' ')

        if channel not in self._namescallback:
            return

        n = self._namescallback[channel][1]
        n += nicklist

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        channel = params[1].lower()
        if channel not in self._namescallback:
            return

        callbacks, namelist = self._namescallback[channel]

        for cb in callbacks:
            cb.callback(namelist)

        del self._namescallback[channel]


class YYBotFactory(protocol.ClientFactory):
    """A new protocol instance will be created each time we connect to
    the server. """

    def __init__(self, network, channels, nickname):
        self.network = network
        self.channels = channels
        self.nickname = nickname

    def add_request_handler(self, request_handler):
        self.request_handler = request_handler

    def add_db_manager(self, db_manager):
        self.db_manager = db_manager

    def buildProtocol(self, addr):
        self.protocol = YYBot()
        self.protocol.factory = self
        self.protocol.nickname = self.nickname
        return self.protocol

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        """Connection Failed."""
        reactor.stop()

    def send_message(self, target, message):
        self.protocol.msg(target, message)

        self.db_manager.add_msg(
            self.network,
            target,
            self.nickname,
            message,
        )

    def join_channel(self, channel):
        log.msg("Joining %s" % channel)
        if channel not in self.channels:
            self.protocol.join(channel)

        self.db_manager.add_status(
            self.network,
            channel,
            self.nickname,
            "has joined %s" % channel,
        )

    def leave_channel(self, channel):
        log.msg("Leaving %s" % channel)
        if channel in self.channels:
            self.protocol.leave(channel)

        self.db_manager.add_status(
            self.network,
            channel,
            self.nickname,
            "has left %s" % channel,
        )

    def get_logs(self, network, target, limit):
        '''retrieve logs from the database and return a list of dicts'''
        cursor = self.db_manager.get_cursor()

        cursor.execute('''
            SELECT date, type, nick, target, network, message
            FROM line
            WHERE target = ? AND network = ?
            ORDER BY date DESC
            LIMIT ?
            ;
        ''', (target, network, limit))

        results = cursor.fetchall()
        logs = []

        for row in results:
            if row[1] == 0:
                entry_type = 'msg'
            elif row[1] == 1:
                entry_type = 'action'
            elif row[1] == 2:
                entry_type = 'status'

            entry = {
                'type': entry_type,
                'date': row[0],
                'nick': row[2],
                'target': row[3],
                'network': row[4],
                'message': row[5],
            }
            logs.append(entry)

        return logs
