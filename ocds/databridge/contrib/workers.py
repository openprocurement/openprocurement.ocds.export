import gevent
import logging
from .client import APICLient

logger = logging.getLogger(__name__)


class Fetch(gevent.Greenlet):

    name = 'Fetch'

    def __init__(self, src_queue, dest_queue, config):

        super(Fetch, self).__init__()
        self.client = APICLient(
            config.get('api_key', ''),
            config.get('api_host'),
            config.get('api_version'),
        )
        self.source = src_queue
        self.dest = dest_queue

    def _run(self):
        while True:
            for feed in self.source:
                resp = self.client.fetch(feed)
                self.dest.put(resp)
                gevent.sleep(2)
            gevent.sleep(2)
        return 1
