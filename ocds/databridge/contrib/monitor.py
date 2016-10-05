import gevent
import logging

logger = logging.getLogger(__name__)


class Monitor(object):

    def __init__(self, target, *args, **kwargs):
        self.run_func = target
        try:
            self.name = self.run_func.__name__
        except AttributeError:
            self.name = self.run_func.func.__name__
        self.target_args = args
        self.target_kwargs = kwargs

    def _monitor(self, failed_g):
        msg = failed_g.exception
        logger.fatal('Error {} on {}'.format(msg, self.name))
        failed_g.kill()
        gevent.sleep(1)
        logger.info('Starting {}'.format(self.name))
        self.start()

    def start(self):
        g = gevent.spawn(self.run_func,
                         *self.target_args,
                         **self.target_kwargs)
        g.link(self._monitor)
        self.g = g
