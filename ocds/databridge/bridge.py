import gevent
import logging
from gevent.queue import Queue
from .feed import APIRetreiver
from .contrib.worker import Worker


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
        self.workers = {}

    def add_worker(self, worker):
        try:
            name = worker.__name__
        except AttributeError:
            name = worker.func.__name__
        q = "{}_queue".format(name)
        setattr(self, q, Queue(maxsize=250))
        self.workers[name] = Worker(worker, self.src, getattr(self, q))
        self.src = getattr(self, q)

    def run(self):
        logger.info('Starting databridge')

        for n, w in self.workers.items():
            logger.info('starting {}'.format(n))
            w.start()
        gevent.joinall([w.g for w in self.workers.values()])
