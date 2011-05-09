"""short url to long url resolver

Example:

    $ python longurl.py http://is.gd/EL4IHc apple.com msn.com
    http://apple.com -> http://www.apple.com/
    http://is.gd/EL4IHc -> http://j.mp/LmvF
    http://www.apple.com/ -> None
    http://j.mp/LmvF -> http://google.com/
    http://msn.com -> http://www.msn.com/
    http://google.com/ -> http://www.google.com/
    http://www.google.com/ -> http://www.google.com.bo/
    http://www.msn.com/ -> http://latam.msn.com/?rd=1
    http://www.google.com.bo/ -> None
    http://latam.msn.com/?rd=1 -> None

"""
from twisted.internet.defer import Deferred, DeferredList
from twisted.web.client import Agent
from twisted.web.http_headers import Headers


class LocationResolver(object):

    defaultHeaders = (
        ('User-Agent', ['LocationResolver/1.0']),
        ('X-Author', ['darkrho@gmail.com']),
        ('X-Version', ['1.0']),
    )

    def __init__(self, reactor):
        self.reactor = reactor
        self.agent = Agent(reactor)

    def resolve(self, shortUrl):
        req  = self.agent.request(
            'HEAD',
            shortUrl,
            Headers(dict(self.defaultHeaders)),
        )
        d = Deferred()
        req.addCallback(self.gotHeaders, d)
        req.addErrback(self.handleError, d)
        return d

    def gotHeaders(self, response, cbFinish):
        value = response.headers.getRawHeaders('Location', [None])[0]
        self.reactor.callLater(0, cbFinish.callback, value)

    def handleError(self, failure, cbFinish):
        self.reactor.callLater(0, cbFinish.errback, failure)


if __name__ == '__main__':
    import sys
    from twisted.internet import reactor

    if len(sys.argv) < 2:
        print("Usage: python {0} <url> [url] ...".format(*sys.argv))
        sys.exit(1)

    resolver = LocationResolver(reactor)

    def handleResult(resolved, url):
        print("{0} -> {1}".format(url, resolved))
        if resolved:
            d = resolver.resolve(resolved)
            d.addCallback(handleResult, resolved)
            d.addErrback(printError, resolved)
            return d

    def printError(failure, url):
        print(">>> {0}".format(url))
        failure.printTraceback()

    dlist = []
    for url in sys.argv[1:]:
        if not (
            url.startswith('http://') or
            url.startswith('https://')
        ):
            url = "http://{0}".format(url)
        d = resolver.resolve(url)
        d.addCallback(handleResult, url)
        d.addErrback(printError, url)
        dlist.append(d)

    d = DeferredList(dlist)
    d.addBoth(lambda _: reactor.stop())

    reactor.run()
