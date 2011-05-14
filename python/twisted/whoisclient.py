from twisted.internet import defer
from twisted.internet.protocol import (
    connectionDone,
    ClientCreator,
    Protocol,
)


class WhoisClientProtocol(Protocol):
    """Basic Whois Protocol following RFC3912
    """

    _buffer = None

    def __init__(self, query, finisher):
        self.query = query
        self.finisher = finisher

    def connectionMade(self):
        self._buffer = []
        self.transport.write(self.query + "\r\n")

    def dataReceived(self, data):
        self._buffer.append(data)

    def connectionLost(self, reason=connectionDone):
        if self._buffer:
            self.finisher.callback(''.join(self._buffer))
        else:
            # TODO: if self._waiting NoResponse
            self.finisher.errback(reason)


class WhoisClient(object):
    """Implementation of whois client
    """

    _protocol = WhoisClientProtocol
    _port = 43

    def __init__(self, reactor, host, port=None):
        self._reactor = reactor
        self._host = host
        self._port = port or self._port

    def _connect(self, *proto_args):
        cc = ClientCreator(self._reactor, self._protocol, *proto_args)
        return cc.connectTCP(self._host, self._port)

    def query(self, query):
        d = defer.Deferred()
        self._connect(query, d)
        return d


if __name__ == '__main__':
    import sys
    from twisted.internet import reactor

    try:
        server = sys.argv[2]
    except IndexError:
        server = "whois.crsnic.net"

    try:
        query = sys.argv[1]
    except IndexError:
        query = "google.com"

    client = WhoisClient(reactor, server)
    d = client.query(query)

    d.addCallback(lambda response: sys.stdout.write(response))
    d.addErrback(lambda failure: sys.stderr.write(str(failure)))

    d.addBoth(lambda _: reactor.stop())

    reactor.run()
