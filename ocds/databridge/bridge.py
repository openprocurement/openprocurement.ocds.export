import gevent
import logging
from gevent.queue import Queue
from .feed import APIRetreiver


logger = logging.getLogger(__name__)


class APIDataBridge(object):

    def __init__(self, config, filter_feed=lambda x: x):
        if not isinstance(config, dict):
            raise TypeError(
                "Expected a dict as config, got {}".format(type(config))
            )
        self.retreiver = APIRetreiver(
            config, filter_callback=filter_feed)
        self.workers = {}

    def add_workers(self, workers, config=None):
        src = self.retreiver
        for worker in workers:
            logger.debug('Add worker {}'.format(worker.name))
            setattr(self, "{}_queue".format(worker.name),
                    Queue(maxsize=250))
            self.workers[worker.name] = worker(
                src,
                getattr(self, "{}_queue".format(worker.name)),
                config
            )
            src = getattr(self, "{}_queue".format(worker.name))
            self.dest_queue = src

    def _check(self):
        for g in self.workers.values():
            if g.ready() or g.dead or g.value:
                logger.fatal('{} dead..restarting'.format(g.name))
                g.kill()
                g.start()
            else:
                logger.info("{} still active".format(g.name))

    def run(self):
        logger.debug('{}: starting'.format(self.__class__))
        for g in self.workers.values():
            g.start()
        while True:
            self._check()
            gevent.sleep(3)
