"""Proof of concept of a web service based on longurl resolver

$ curl -s "http://localhost:31337/?url=http://is.gd/EL4IHc" | python -m json.tool
{
        "status": "ok",
        "url": "http://www.google.com.bo/"
}

"""
from cyclone.web import (
    Application,
    RequestHandler,
    asynchronous as async
)

from longurl import LocationResolver


class MainHandler(RequestHandler):

    @async
    def get(self):
        url = self.get_argument('url', '')
        if url:
            return self.resolve(url.encode('utf-8'))
        else:
            self.finish(dict(status='error', message='missing "url" argument'))

    def resolve(self, url):
        d = self.settings.resolver.resolve(url)
        d.addCallback(self.processResponse, url)
        d.addErrback(self.handleError)
        return d

    def processResponse(self, result, url):
        if result:
            return self.resolve(result)
        self.finish(dict(status='ok', url=url))

    def handleError(self, failure):
        try:
            e = failure.value
        except AttributeError:
            self.finish(dict(status='error', message='unknown error'))
        else:
            self.finish(dict(status='error', message=str(e)))


def main(reactor):
    resolver = LocationResolver(reactor)
    application = Application([
            (r'/', MainHandler),
        ],
        xheaders=True,
        resolver=resolver,
    )

    reactor.listenTCP(31337, application)
    reactor.run()


if __name__ == '__main__':
    import sys
    from twisted.internet import reactor
    from twisted.python import log

    log.startLogging(sys.stdout)
    main(reactor)
