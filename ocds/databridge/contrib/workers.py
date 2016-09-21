import gevent
import logging
from .client import APICLient
from ocds.export.release import get_release_from_tender
from ocds.storage import CouchStorage


logger = logging.getLogger(__name__)


class Fetch(gevent.Greenlet):

    name = 'Fetch'

    def __init__(self, src_queue, dest_queue, config):
        super(Fetch, self).__init__()
        config = config['api']
        self.client = APICLient(
            config.get('api_key', ''),
            config.get('api_host'),
            config.get('api_version'),
        )
        self.source = src_queue
        self.dest = dest_queue

    def _run(self):
        logger.info('Starting: {}'.format(self.name))
        while True:
            for feed in self.source:
                resp = self.client.fetch(feed)
                self.dest.put(resp)
                gevent.sleep(0.5)
            gevent.sleep(2)
        return 1


class Parse(gevent.Greenlet):
    name = "Parse"

    def __init__(self, src_queue, dest_queue, config):
        super(Parse, self).__init__()
        self.prefix = config['release'].get('prefix')
        self.source = src_queue
        self.dest = dest_queue

    def _run(self):
        logger.info('Starting: {}'.format(self.name))
        while True:
            for feed in self.source:
                for tender in feed:
                    try:
                        release = get_release_from_tender(tender, self.prefix)
                        logger.info("{} generated release".format(len(release)))
                        self.dest.put(release)
                    except Exception as e:
                        logger.fatal('Error {} during generation release'.format(e))
                gevent.sleep(0.5)
            gevent.sleep(2)
        return 1


class Save(gevent.Greenlet):

    name = "Save"

    def __init__(self, src_queue, dest_queue, config):

        super(Save, self).__init__()
        self.storage = config.get('storage')
        self.source = src_queue
        self.dest = dest_queue

    def _run(self):
        logger.info('Starting: {}'.format(self.name))
        while True:
            for release in self.source:
                self.dest.put('Save doc; {}'.format(release['id']))
                self.storage.save(release)
        gevent.sleep(2)
