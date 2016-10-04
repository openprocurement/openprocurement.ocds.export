import gevent
import logging
from gevent.queue import Queue
from .feed import APIRetreiver
from .contrib.client import APIClient
from ocds.export.release import get_release_from_tender
from ocds.storage import CouchStorage


logger = logging.getLogger(__name__)


class APIDataBridge(object):

    def __init__(self, config, filter_feed=lambda x: x):
        if not isinstance(config, dict):
            raise TypeError(
                "Expected a dict as config, got {}".format(type(config))
            )
        self.storage = CouchStorage(config['db'])
        self.retreiver = APIRetreiver(
            config['api'], filter_callback=filter_feed)

        self.tenders_client = APIClient(
            config['api']['api_key'],
            config['api']['api_host'],
            config['api']['api_version']
        )
        self.to_save_queue = Queue(maxsize=250)
        self.to_parse_queue = Queue(maxsize=250)
        self.prefix = config['release'].get('prefix')

    def fetch_tenders(self):
        logger.info('Starting upload worker')
        while True:
            for feed in self.retreiver:
                resp = self.tenders_client.fetch(feed)
                if resp:
                    logger.info('fetched {} tenders'.format(len(resp)))
                self.to_parse_queue.put(resp)
                gevent.sleep(0.5)
            gevent.sleep(1)

    def create_releases(self):
        logger.info('Starting generating releases')
        while True:
            if self.to_parse_queue.empty():
                logger.info('parse queue empty')
                gevent.sleep(5)
            for feed in self.to_parse_queue:
                for tender in feed:
                    try:
                        release = get_release_from_tender(tender, self.prefix)
                        logger.info("generated release for tender "
                                    "{}".format(tender['id']))
                        self.to_save_queue.put(release)
                    except Exception as e:
                        logger.fatal('Error {} during'
                                     ' generation release'.format(e))
                gevent.sleep(0.5)
            gevent.sleep(2)

    def save_releases(self):
        logger.info('Starting saving')
        while True:
            for release in self.to_save_queue:
                logger.info('Save doc; {}'.format(release['id']))
                self.storage.save(release)
        gevent.sleep(2)

    def run(self):
        logger.info('Starting databridge')
        gs = [
            gevent.spawn(self.fetch_tenders),
            gevent.spawn(self.create_releases),
            gevent.spawn(self.save_releases),
        ]
        for g in gs:
            g.start()
        while True:
            for g in gs:
                try:
                    g.get(block=False)
                    logger.info('{} down! Restarting'.format(g))
                    g.start()
                except gevent.Timeout:
                    logger.info('{} still active'.format(g.__class__))
            gevent.sleep(3)
