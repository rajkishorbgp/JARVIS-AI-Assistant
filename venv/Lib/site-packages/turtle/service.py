from twisted.application import service
from twisted.python import log

try:
    # windows doesn't support syslog; so ok to pass
    import syslog

    class SyslogObserver:
        def __init__(self, prefix):
            self.prefix = prefix
            syslog.openlog(prefix, 0, syslog.LOG_LOCAL1)

        def emit(self, eventDict):
            edm = eventDict['message']
            if not edm:
                if eventDict['isError'] and eventDict.has_key('failure'):
                    text = eventDict['failure'].getTraceback()
                elif eventDict.has_key('format'):
                    text = eventDict['format'] % eventDict
                else:
                    # we don't know how to log this
                    return
            else:
                text = ' '.join(map(str, edm))

            lines = text.split('\n')
            while lines[-1:] == ['']:
                lines.pop()

            firstLine = 1
            for line in lines:
                if firstLine:
                    firstLine=0
                else:
                    line = '\t%s' % line
                syslog.syslog(syslog.LOG_INFO, '[%s] %s' % (self.prefix, line))

    def startLogging(prefix='Twisted', setStdout=1):
        obs = SyslogObserver(prefix)
        log.startLoggingWithObserver(obs.emit, setStdout=setStdout)
except:
    syslog = None



def makeService(options):
    """
    Create the service for the application
    """
    return TurtleService(options)



class TurtleService(service.Service):
    """
    I am the service responsible for starting up a TurtleProxy
    instance with a command line given configuration file.
    """
    def __init__(self, options):
        self.config = options['config']
        self.syslog_prefix = options['with_syslog_prefix']

    def startService(self):
        """
        Before reactor.run() is called we setup the system.
        """
        service.Service.startService(self)
        try:
            if self.syslog_prefix and syslog:
                startLogging(self.syslog_prefix)

            from turtle import proxy, config
            urlmap, filter_rest, port = config.loadConfigFromFile(self.config)
            log.msg('Initializing turtle...')
            log.msg("Domains: %s" % (", ".join(urlmap.keys())))
            desc = "Allowing"
            if filter_rest:
                desc = "Filtering"
            log.msg("%s unknown domains" % (desc,))
            f = proxy.TurtleHTTPFactory(urlmap, filter_rest)
            from twisted.internet import reactor
            reactor.listenTCP(port, f)
        except:
            import traceback
            print traceback.format_exc()
            raise
