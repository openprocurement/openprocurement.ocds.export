import gevent
import logging
from gevent.queue import Queue
from .contrib.retreive import RetreiverForward, RetreiverBackward
from .contrib.client import get_retreive_clients
from .helpers import get_start_point


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

    def __iter__(self):
        self._start()
        while True:
            forward, backward = self.workers
            if backward.ready():
                logger.info('Backward ready')
                if backward.value != 1:
                    logger.info('Backward fails')
                    self._restart()
            if forward.dead or forward.ready():
                self._restart()
            if self.tender_queue.empty():
                gevent.sleep(1)
            yield self.tender_queue.get()
