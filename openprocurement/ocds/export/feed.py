import gevent
import logging
import functools
from gevent.queue import Queue
from openprocurement.ocds.export.helpers import get_start_point
from .contrib.retreive import retreiver
from .contrib.client import get_retreive_clients


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

    def _start(self):
        logger.info('Retreivers starting')
        self.forward_client, self.backward_client = get_retreive_clients(
            self.api_key,
            self.api_host,
            self.api_version
        )
        self.forward = functools.partial(retreiver, self.forward_client)
        self.backward = functools.partial(retreiver, self.backward_client)

        forward_params, backward_params = get_start_point(
            self.forward_client,
            self.backward_client,
            self.tender_queue,
            self.filter_callback,
            self.api_extra_params
        )

        fg = gevent.spawn(
            self.forward,
            forward_params,
            self.tender_queue,
            self.filter_callback,
        )
        bg = gevent.spawn(
            self.backward,
            backward_params,
            self.tender_queue,
            self.filter_callback,
            name='backward'
        )
        self.workers = [fg, bg]

    def _restart(self):
        logger.warn('Restarting retreivers')
        for g in self.workers:
            g.kill()
        self._start()

    def __iter__(self):
        self._start()
        while True:
            forward, backward = self.workers
            if backward.ready() or backward.dead:
                if backward.value != 1:
                    logger.fatal('Backward fails')
                    self._restart()
            if forward.dead or forward.ready():
                logger.warm('Forward worker died!')
                self._restart()
            if self.tender_queue.empty():
                gevent.sleep(1)
            yield self.tender_queue.get()
