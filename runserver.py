import sys
import helpers.ssl_helper as ssl_helper
from twisted.python import log
from bot.yybot import YYBotFactory
from server.request_handler import RequestHandlerFactory
from logger.sqlite_handler import SQLiteHandler

if __name__ == '__main__':
    try:
        # not available on Mac OS
        from twisted.internet import pollreactor
        pollreactor.install()
    except:
        pass

    from twisted.internet import ssl, reactor

    # initialize logging
    log.startLogging(sys.stdout)
    ssl_helper.prepare_ssl_cert()

    request_handler = RequestHandlerFactory()
    channels = ["#yychat"]
    network = 'irc.freenode.net'

    irc_bot_factory = YYBotFactory(network, channels, "yychat")
    request_handler.add_irc_bot(irc_bot_factory)
    irc_bot_factory.add_request_handler(request_handler)

    db_manager = SQLiteHandler('log.sqlite3')
    irc_bot_factory.add_db_manager(db_manager)

    contextFactory = ssl.ClientContextFactory()

    reactor.connectSSL(
        network,
        6697,
        irc_bot_factory,
        contextFactory,
    )

    with open(ssl_helper.get_cert_path()) as keyAndCert:
        cert = ssl.PrivateCertificate.loadPEM(keyAndCert.read())

    cert_options = cert.options()
    reactor.listenSSL(10100, request_handler, cert_options)

    reactor.run()
