import urlparse

from twisted.internet import reactor, defer, error
from twisted.web import proxy, http
from twisted.python import log

class TurtleProxyClientFactory(proxy.ProxyClientFactory):
    """
    Redefine the L{proxy.ProxyClientFactory} in order to trigger
    the L{TurtleProxyRequest.completed} deferred once the connection
    has been closed.
    """
    def clientConnectionLost(self, connector, reason):
        proxy.ProxyClientFactory.clientConnectionLost(self, connector, reason)
        if reason.trap(error.ConnectionDone):
            self.father.completed.callback(None)
        else:
            self.father.completed.errback(reason)

class TurtleProxyRequest(proxy.ProxyRequest):
    """
    Redefine L{proxy.ProxyRequest} to add support for upcalling the
    factory to decide whether to forward or filter a specific request.
    If the request is blocked then return an error page to the client.

    Also introduce a deferred that is fired once the forwarded host
    request has completed, so that we can unlock the caller that could
    be waiting for that to be over.

    @ivar completed: a L{defer.Deferred} that is triggered once the
                        outgoing request has completed.
    """

    protocols = {'http': TurtleProxyClientFactory}

    def __init__(self, channel, queued, reactor=reactor):
        proxy.ProxyRequest.__init__(self, channel, queued, reactor)
        self.completed = defer.Deferred()

    def process(self):
        parsed = urlparse.urlparse(self.uri)
        protocol = parsed[0]
        host = parsed[1]
        port = self.ports[protocol]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        rest = urlparse.urlunparse(('', '') + parsed[2:])
        if not rest:
            rest = rest + '/'
        class_ = self.protocols[protocol]
        headers = self.getAllHeaders().copy()
        priority = headers.pop('x-priority', False)

        if 'host' not in headers:
            headers['host'] = host
        self.content.seek(0, 0)
        s = self.content.read()
        clientFactory = class_(self.method, rest, self.clientproto,
                               headers, s, self)

        processed = self.channel.factory.process(host, port, clientFactory,
                                                 priority, self.completed)
        if not processed:
            self.sendError('''<H1>%s domain is filtered</H1>''' % (host,))

        else:
            processed.addErrback(self.sendError)

    def sendError(self, line):
        self.transport.write("HTTP/1.0 501 Gateway error\r\n")
        self.transport.write("Content-Type: text/html\r\n")
        self.transport.write("\r\n")
        self.transport.write(str(line))
        self.transport.loseConnection()


class TurtleProxy(proxy.Proxy):
    requestFactory = TurtleProxyRequest

class TurtleHTTPFactory(http.HTTPFactory):
    """
    Override the default HTTPFactory to add support for a shared (among
    all incoming requests) mapping of urls to request throttlers.

    There is one factory for all incoming connections so shared state has
    to stay here.

    @ivar urlmapping: A C{dict} that maps hostnames to instances of
                            L{turtle.engine.ThrottlingDeferred}.

    @ivar filter_rest: Define the behavior of unknown urls. If C{True}
                        block those requests.
    """

    protocol = TurtleProxy

    def __init__(self, urlmapping={}, filter_rest=False, reactor=reactor):
        http.HTTPFactory.__init__(self)
        self.urlmapping = urlmapping
        self.filter_rest = filter_rest
        self.reactor = reactor

    def process(self, host, port, clientFactory, priority, completed):
        """
        Process a request from the Proxy object. Check if it's in the
        mapping for urls so that we can use the limits specified in the
        configuration file. If there is not then check if we can forward
        unknown hosts, and if we cannot block them. If priority is high
        this request is scheduled in front of the queue of waiting requests
        and will use the next slot available.
        """
        if host in self.urlmapping:
            throttler = self.urlmapping[host]
            if priority:
                fun = throttler.runasap
            else:
                fun = throttler.run
            return fun(self.makeRequest, host, port, clientFactory, completed)

        else:
            if self.filter_rest:
                log.msg("Filtering %s:%s..." % (host, port))
                return False
            else:
                return self.makeRequest(host, port, clientFactory, completed)

    def makeRequest(self, host, port, clientFactory, completed):
        """
        Abstract the function away so that we can use it both directly
        for unfiltered calls and through the throttling engine or other
        similar calls.
        """
        log.msg("Proxying %s:%s..." % (host, port))
        self.reactor.connectTCP(host, port, clientFactory)
        return completed
