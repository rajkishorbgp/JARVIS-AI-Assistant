from twisted.test.proto_helpers import StringTransportWithDisconnection, LineSendingProtocol

from twisted.python import failure
from twisted.internet import defer, error
from twisted.trial import unittest
from turtle import proxy

from twisted.web.test.test_proxy import FakeReactor, DummyParent, DummyChannel

class TestEngine(unittest.TestCase):

    def setUp(self):
        self.counter = 0

    def _incr(self, result, by=1):
        self.counter += by
        return result

    def trap(self, failure, what):
        failure.trap(what)

    def testConnectionDone(self):
        """
        C{TurtleProxyClientFactory} calls the father's completed
        deferred after clientConnectionLost is called.
        """
        class Father(object):
            def __init__(self):
                self.completed = defer.Deferred()

        f = Father()
        f.completed.addCallback(self._incr)
        t = proxy.TurtleProxyClientFactory("GET", "/", "1.0", {}, "", f)
        t.clientConnectionLost(object(), failure.Failure(error.ConnectionDone()))
        self.assertEquals(self.counter, 1)

        ## f = Father()
        ## t = proxy.TurtleProxyClientFactory("GET", "/", "1.0", {}, "", f)
        ## t.clientConnectionLost(object(), failure.Failure(error.ConnectionLost()))
        ## self.assertFailure(f.completed, error.ConnectionLost)
        ## self.assertEquals(self.counter, 1)

# This test cases were taken almost verbatim from Twisted Matrix
# http://www.twistedmatrix.com
class TurtleProxyRequestTestCase(unittest.TestCase):
    """
    Tests for L{TurtleProxyRequest}.
    """

    def _testProcess(self, uri, expectedURI, method="GET", data=""):
        """
        Build a request pointing at C{uri}, and check that a proxied request
        is created, pointing a C{expectedURI}.
        """
        transport = StringTransportWithDisconnection()
        channel = DummyChannel(transport)
        reactor = FakeReactor()
        proxy_factory = proxy.TurtleHTTPFactory({}, False, reactor)
        channel.factory = proxy_factory
        request = proxy.TurtleProxyRequest(channel, False, reactor)
        request.gotLength(len(data))
        request.handleContentChunk(data)
        request.requestReceived(method, 'http://example.com%s' % (uri,),
                                'HTTP/1.0')

        self.assertEquals(len(reactor.connect), 1)
        self.assertEquals(reactor.connect[0][0], "example.com")
        self.assertEquals(reactor.connect[0][1], 80)

        factory = reactor.connect[0][2]
        self.assertIsInstance(factory, proxy.TurtleProxyClientFactory)
        self.assertEquals(factory.command, method)
        self.assertEquals(factory.version, 'HTTP/1.0')
        self.assertEquals(factory.headers, {'host': 'example.com'})
        self.assertEquals(factory.data, data)
        self.assertEquals(factory.rest, expectedURI)
        self.assertEquals(factory.father, request)


    def test_process(self):
        """
        L{TurtleProxyRequest.process} should create a connection to the given server,
        with a L{TurtleProxyClientFactory} as connection factory, with the correct
        parameters:
            - forward comment, version and data values
            - update headers with the B{host} value
            - remove the host from the URL
            - pass the request as parent request
        """
        return self._testProcess("/foo/bar", "/foo/bar")


    def test_processWithoutTrailingSlash(self):
        """
        If the incoming request doesn't contain a slash,
        L{TurtleProxyRequest.process} should add one when instantiating
        L{TurtleProxyClientFactory}.
        """
        return self._testProcess("", "/")


    def test_processWithData(self):
        """
        L{TurtleProxyRequest.process} should be able to retrieve request body and
        to forward it.
        """
        return self._testProcess(
            "/foo/bar", "/foo/bar", "POST", "Some content")


    def test_processWithPort(self):
        """
        Check that L{TurtleProxyRequest.process} correctly parse port in the incoming
        URL, and create a outgoing connection with this port.
        """
        transport = StringTransportWithDisconnection()
        channel = DummyChannel(transport)
        reactor = FakeReactor()
        proxy_factory = proxy.TurtleHTTPFactory({}, False, reactor)
        channel.factory = proxy_factory

        request = proxy.TurtleProxyRequest(channel, False, reactor)
        request.gotLength(0)
        request.requestReceived('GET', 'http://example.com:1234/foo/bar',
                                'HTTP/1.0')

        # That should create one connection, with the port parsed from the URL
        self.assertEquals(len(reactor.connect), 1)
        self.assertEquals(reactor.connect[0][0], "example.com")
        self.assertEquals(reactor.connect[0][1], 1234)


    def test_filtering(self):
        """
        Check that L{TurtleProxyRequest.process} filters urls that
        it doesn't know.
        """
        class FakeThrottler(object):
            called_run = False
            called_run_asap = False
            def run(self, fun, *args, **kwargs):
                self.called_run = True
                return defer.maybeDeferred(fun, *args, **kwargs)

            def runasap(self, fun, *args, **kwargs):
                self.called_run_asap = True
                return defer.maybeDeferred(fun, *args, **kwargs)


        transport = StringTransportWithDisconnection()
        transport.protocol = LineSendingProtocol([], False)
        channel = DummyChannel(transport)
        reactor = FakeReactor()

        throttler = FakeThrottler()
        urlmap = {'delicious.com': throttler}
        proxy_factory = proxy.TurtleHTTPFactory(urlmap, True, reactor)
        channel.factory = proxy_factory

        request = proxy.TurtleProxyRequest(channel, False, reactor)
        request.gotLength(0)
        request.requestReceived('GET', 'http://example.com:1234/foo/bar',
                                'HTTP/1.0')

        # That should create one connection, with the port parsed from the URL
        self.assertEquals(len(reactor.connect), 0)


        request = proxy.TurtleProxyRequest(channel, False, reactor)
        request.gotLength(0)
        request.requestReceived('GET', 'http://delicious.com:1234/foo/bar',
                                'HTTP/1.0')

        # That should create one connection, with the port parsed from the URL
        self.assertEquals(len(reactor.connect), 1)
        self.assertEquals(reactor.connect[-1][0], "delicious.com")
        self.assertEquals(reactor.connect[-1][1], 1234)
        self.assertEquals(throttler.called_run, True)
        self.assertEquals(throttler.called_run_asap, False)




        request = proxy.TurtleProxyRequest(channel, False, reactor)
        request.gotLength(0)
        request.requestHeaders.addRawHeader('x-priority', 'interactive')
        request.requestReceived('GET', 'http://delicious.com:1234/foo/bar',
                                'HTTP/1.0')

        # That should create one connection, with the port parsed from the URL
        self.assertEquals(len(reactor.connect), 2)
        self.assertEquals(reactor.connect[-1][0], "delicious.com")
        self.assertEquals(reactor.connect[-1][1], 1234)
        self.assertEquals(throttler.called_run_asap, True)

