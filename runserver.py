from twisted.internet import reactor
from twisted.python import log

import sys
from bot.yybot import YYBotFactory

if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = YYBotFactory("#yychat", "yychat")

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
