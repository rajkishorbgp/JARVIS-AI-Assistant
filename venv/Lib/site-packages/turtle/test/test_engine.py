from twisted.internet import defer
from twisted.trial import unittest
from turtle import engine

class TestEngine(unittest.TestCase):

    def _incr(self, result, by=1):
        self.counter += by

    def setUp(self):
        self.counter = 0

    def testThrottler(self):
        N = 13
        thr = engine.ThrottlingDeferred(3*N, N, 200)
        self.assert_(thr._resetLoop.running)
        thr._resetLoop.stop()
        self.assert_(not thr._resetLoop.running)

        controlDeferred = defer.Deferred()
        def helper(self, arg):
            self.arg = arg
            return controlDeferred

        results = []
        uniqueObject = object()
        resultDeferred = thr.run(helper, self=self, arg=uniqueObject)
        resultDeferred.addCallback(results.append)
        resultDeferred.addCallback(self._incr)
        self.assertEquals(results, [])
        self.assertEquals(self.arg, uniqueObject)
        controlDeferred.callback(None)
        self.assertEquals(results.pop(), None)
        self.assertEquals(self.counter, 1)

        thr._reset()
        self.counter = 0
        for i in range(1, 1 + N):
            thr.acquire().addCallback(self._incr)
            self.assertEquals(self.counter, i)

        thr.acquire().addCallback(self._incr)
        self.assertEquals(self.counter, N)
        self.assertEquals(thr.points, 0)

        for i in range(1, N):
            thr.acquire().addCallback(self._incr)
            self.assertEquals(self.counter, N)

        # Scheduled a prioritized call for last and
        # later we'll check that this runs through
        # before everything else.
        thr.acquire(True).addCallback(self._incr, 10)

        # Even if I release a lot, nothing happens
        # until I have enough points to unlock the
        # situation in the throttler
        for i in thr.waiting:
            self.assertEquals(thr.points, 0)
            thr.release()
        self.assertEquals(self.counter, N)
        self.assertEquals(thr.points, 0)

        # At this point I have: 14 waiting calls (N + 1)
        # and 0 points. After I reset I'll have 13 waiting
        # calls and 12 points.
        thr._reset()
        self.assertEquals(self.counter, N+10)
        self.assertEquals(thr.points, 12)

        # As I said 13 waiting and 12 points:
        for i in range(len(thr.waiting)):
            thr.release()

        self.assertEquals(thr.points, 0)
        self.assertEquals(self.counter, N*2+9)

        # Now there's one waiting and 0 points
        thr._reset()

        # The last reset also called a release
        # 0 waiting and 12 points
        self.assertEquals(self.counter, 2*N+10)
        self.assertEquals(thr.points, N-1)
