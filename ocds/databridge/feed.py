import gevent
import logging
import sys
from gevent.queue import Queue
from .contrib.retreive import RetreiverForward, RetreiverBackward
from .contrib.client import get_retreive_clients
from .helpers import get_start_point


QUEUE_FULL_DELAY = 5
EMPTY_QUEUE_DELAY = 1
ON_EMPTY_DELAY = 10
FORWARD_WORKER_SLEEP = 5
BACKWARD_WOKER_DELAY = 1
WATCH_DELAY = 1

logger = logging.getLogger(__name__)


class APIRetreiver(object):

    def __init__(self, config, filter_callback=lambda x: x):
        if not isinstance(config, dict):
            raise TypeError(
                "Expected a dict as config, got {}".format(type(config))
            )
        self.api_host = config.get('api_host')
        self.api_version = config.get('api_version')
        self.api_key = config.get('api_key')
        self.api_extra_params = config.get('api_extra_params')

        self.tender_queue = Queue(maxsize=config.get('queue_max_size', 250))
        self.filter_callback = filter_callback
        self.origin_cookie, self.forward_client, self.backward_client = get_retreive_clients(
            self.api_key,
            self.api_host,
            self.api_version
        )

    def _start(self):
        logger.info('{} starting'.format(self.__class__))
        forward, backward = get_start_point(
            self.forward_client,
            self.backward_client,
            self.origin_cookie,
            self.tender_queue,
            self.filter_callback,
            self.api_extra_params
        )
        forward_worker = RetreiverForward(
            self.forward_client,
            forward,
            self.origin_cookie,
            self.tender_queue,
            self.filter_callback,
            logger
        )
        backward_worker = RetreiverBackward(
            self.backward_client,
            backward,
            self.origin_cookie,
            self.tender_queue,
            self.filter_callback,
            logger
        )
        forward_worker.start()
        backward_worker.start()
        self.workers = [forward_worker, backward_worker]

    def _restart(self):
        for g in self.workers:
            g.kill()
        self._start()

    def _check(self):
        forward, backward = self.workers

        if backward.ready():
            if backward.value != 1:
                self._restart()
                return
        if forward.dead or forward.ready():
            self._restart()

    def __iter__(self):
        try:
            self._start()
        except Exception as e:
            logger.error('Error during start {}'.format(e))
            sys.exit(2)
        while True:
            self._check()
            while not self.tender_queue.empty():
                yield self.tender_queue.get()
            gevent.sleep(0.5)
