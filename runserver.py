from twisted.python import log

import sys
from bot.yybot import YYBotFactory
from server.request_handler import RequestHandlerFactory

if __name__ == '__main__':
    try:
        # not available on Mac OS
        from twisted.internet import pollreactor
        pollreactor.install()
    except:
        pass

    from twisted.internet import reactor

    # initialize logging
    log.startLogging(sys.stdout)

    request_handler = RequestHandlerFactory()
    irc_bot = YYBotFactory("#yychat", "yychat")
    request_handler.add_irc_bot(irc_bot)
    irc_bot.add_request_handler(request_handler)

    reactor.connectTCP("irc.freenode.net", 6667, irc_bot)
    reactor.listenTCP(10100, request_handler)

    reactor.run()
