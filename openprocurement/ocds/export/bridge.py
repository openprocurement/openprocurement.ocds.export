import logging
import gevent
import gevent.pool
import jsonpatch
from requests.exceptions import HTTPError
from functools import partial
from gevent.queue import Queue
from .feed import APIRetreiver
from .contrib.client import APIClient
from .storage import TendersStorage
from .helpers import exists_or_modified


logger = logging.getLogger(__name__)


class APIDataBridge(object):

    def __init__(self, config):
        if not isinstance(config, dict):
            raise TypeError(
                "Expected a dict as config, got {}".format(type(config))
            )
        self._db = TendersStorage(config['tenders_db']['url'],
                                  config['tenders_db']['name'])

        self.tenders_queue = Queue(maxsize=500)
        self.historical = config.get('historical', False)
        self.retreiver = APIRetreiver(
            config['api'],
            filter_callback=partial(exists_or_modified, self._db)
        )
        self.client = APIClient(
            config['api']['api_key'],
            config['api']['api_host'],
            config['api']['api_version'],
            historical=self.historical
        )

        self.fetch_pool = gevent.pool.Pool(20)

    def prepare_pached(self, tenders, version, first=True):
        if first:
            first_tender = tenders[0]
            tenders = tenders[1:]
        else:
            first_tender = self._db.get(tenders[0].get('id'))
        origin = first_tender.copy()
        patches = first_tender.pop('patches', [])
        if patches:
            for patch in patches:
                first_tender = jsonpatch.apply_patch(first_tender, patch)
        for tender in tenders:
            if not tender:
                continue
            patch = jsonpatch.make_patch(first_tender, tender).patch
            if patch:
                patches.append(patch)
            first_tender = tender
        origin['patches'] = patches
        origin['version'] = version
        origin['_id'] = origin['id']
        return origin

    def fetch_tender_versioned(self, feed_item):
        _id = feed_item['id']
        version, tender = self.client.get_tender(_id)
        logger.info('Got tender id={}, version={}'.format(tender['id'], version))
        last_date_modified = self._db.view('tenders/by_dateModified', key=tender['id']).rows
        first = False if last_date_modified else True
        last_version = 1 if first else self._db.get(_id).get('version')
        try:
            revisions = []
            for i in range(int(last_version), int(version)):
                try:
                    gversion, tender = self.client.get_tender(_id, str(i))
                except:
                    break
                if gversion == str(i):
                    logger.info('Got tender id={} revision {}'.format(_id, i))
                    revisions.append(tender)
            revisions.append(tender)
        except HTTPError:
            logger.fatal("Falied to retreive tender id={} \n"
                         "version {}".format(tender['id'], version))
        logger.info('Finishing fetching revisions of {}'.format(_id))
        self.tenders_queue.put(self.prepare_pached(revisions, version,
                                                   first=first))

    def save_items(self):
        logger.info('Start saving')
        while True:
            for item in self.tenders_queue:
                if item['id'] in self._db:
                    doc = self._db.get(item['id'])
                    item['_rev'] = doc['_rev']
                item['doc_type'] = 'Tender'
                self._db.save(item)
                logger.info('Saved doc {}'.format(item['id']))
            gevent.sleep(1)

    def fetch_tenders(self):
        logger.info('Starting downloading tenders')
        while True:
            for feed in self.retreiver:
                if not feed:
                    break
                if self.historical:
                    self.fetch_pool.map(self.fetch_tender_versioned, feed)
                    continue
                else:
                    tenders = self.fetch_pool.map(self.client.get_tender, [x['id'] for x in feed])
                if tenders:
                    logger.info('Fetched {} tenders'.format(len(tenders)))
                    for t in tenders:
                        if t[1]:
                            self.tenders_queue.put(t[1])
            gevent.sleep(0.5)

    def _restart(self, gr):
        for g in self.jobs:
            g.kill()
        self.jobs = [
            gevent.spawn(self.fetch_tenders),
            gevent.spawn(self.save_items)
        ]
        for j in self.jobs:
            j.link_exception(self._restart)

    def run(self):
        while True:
            self.jobs = [
                gevent.spawn(self.fetch_tenders),
                gevent.spawn(self.save_items)
            ]
            for j in self.jobs:
                j.link_exception(self._restart)

            gevent.joinall(self.jobs)
            gevent.sleep(1)
