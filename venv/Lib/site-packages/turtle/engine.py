from twisted.internet import defer, task

class _ConcurrencyPrimitive(object):
    _execute = defer.maybeDeferred

    def __init__(self):
        self.waiting = []

    def _releaseAndReturn(self, r):
        self.release()
        return r

    def run(*args, **kwargs):
        """Acquire, run, release.

        This function takes a callable as its first argument and any
        number of other positional and keyword arguments.  When the
        lock or semaphore is acquired, the callable will be invoked
        with those arguments.

        The callable may return a Deferred; if it does, the lock or
        semaphore won't be released until that Deferred fires.

        @return: Deferred of function result.
        """
        if len(args) < 2:
            if not args:
                raise TypeError("run() takes at least 2 arguments, none given.")
            raise TypeError("%s.run() takes at least 2 arguments, 1 given" % (
                args[0].__class__.__name__,))
        self, f = args[:2]
        args = args[2:]

        def execute(ignoredResult):
            d = self._execute(f, *args, **kwargs)
            d.addBoth(self._releaseAndReturn)
            return d

        d = self.acquire(kwargs.pop('_hpriority', False))
        d.addCallback(execute)
        return d

    def runasap(*args, **kwargs):
        """Acquire, run, release and put in the front of the waiting queue

        @return: Deferred of function result.
        """
        kwargs['_hpriority'] = True
        return _ConcurrencyPrimitive.run(*args, **kwargs)

class ThrottlingDeferred(_ConcurrencyPrimitive):
    def __init__(self, concurrency, calls, interval):
        """
        Throttling deferred that considers both the concurrency
        requirements and the frequency, over time, of calls that
        you are allowed to make. It's clear however that if the
        rate of calls is higher than the tokens there will be
        a queue, and the queue can grow indefinitely if calls don't
        return quickly enough. More specifically: if T(f) is the
        time it takes to execute a call, and this time is formed
        by Ts(f) and Tp(f) [serial time and parallelizable time]:

            Ts(f)*calls + Tp(f)*(calls/tokens) <= interval

        If this is not true then the ingress could be too high
        and causing an ever-increasing queue.

        @param concurrency: The maximum number of concurrent
                            calls.
        @type concurrency: C{int}

        @param calls: Represents the number of calls that
                can be made every C{interval}
        @type calls: C{int}

        @param interval: Represents the time between a
                C{calls} number of calls

        NOTE: Currently it's not a requirement but if distributed
                usage of this deferred was a necessity, the points
                and current concurrency levels should be stored
                somewhere else and updated every time they are
                checked (there would also be race conditions and
                so on).
        """
        _ConcurrencyPrimitive.__init__(self)

        self._sem = defer.DeferredSemaphore(concurrency)
        self._execute = self._sem.run

        self.calls = calls
        self.interval = interval
        self.points = calls

        self._resetLoop = task.LoopingCall(self._reset)
        self._resetLoop.start(interval, now=False)

    def _reset(self):
        self.points = self.calls
        self.release()

    def acquire(self, priority=False):
        """Attempt to acquire the token.

        @param priority: Defines an high priority call that should
                            either be executed immediately or scheduled
                            as the immediate next one.
        @type priority: C{bool}

        @return: a Deferred which fires on token acquisition.
        """
        assert self.points >= 0, "Internal inconsistency??  points should never be negative"

        d = defer.Deferred()
        if not self.points:
            if priority:
                # Think about a better data structure for this
                self.waiting.insert(0, d)
            else:
                self.waiting.append(d)
        else:
            self.points = self.points - 1
            d.callback(self)
        return d

    def release(self):
        """Release the token.

        Should be called by whoever did the acquire() when the shared
        resource is free.
        """
        if self.points > 0 and self.waiting:
            self.points = self.points - 1
            d = self.waiting.pop(0)
            d.callback(self)

