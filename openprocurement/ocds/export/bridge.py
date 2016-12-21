import gevent
import logging
from gevent.queue import Queue
from .feed import APIRetreiver
from .contrib.monitor import Monitor


logger = logging.getLogger(__name__)


class APIDataBridge(object):

    def __init__(self, config, filter_feed=lambda x: x):
        if not isinstance(config, dict):
            raise TypeError(
                "Expected a dict as config, got {}".format(type(config))
            )
        self.retreiver = APIRetreiver(
            config['api'], filter_callback=filter_feed)

        self.src = self.retreiver
        self.jobs = {}

    def add_gt(self, func, last=False, side_effect=None):
        try:
            name = func.__name__
        except AttributeError:
            name = func.func.__name__
        q = None
        if not last:
            setattr(self, "{}_queue".format(name), Queue(maxsize=250))
            q = getattr(self, "{}_queue".format(name))
        self.jobs[name] = Monitor(func, self.src, q)
        if not last:
            self.src = q

    def run(self):
        logger.info('Starting databridge')
        for n, w in self.jobs.items():
            logger.info('starting {}'.format(n))
            w.start()
        gevent.joinall([w.g for w in self.jobs.values()])
