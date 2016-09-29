import gevent
import logging
from requests.adapters import HTTPAdapter
from .exceptions import LBMismatchError
from ocds.export.release import get_release_from_tender


APIAdapter = HTTPAdapter(max_retries=5,
                         pool_connections=50,
                         pool_maxsize=30)

logger = logging.getLogger(__name__)


def get_start_point(forward, backward, cookie, queue, callback=lambda x: x, extra={}):
    forward_params = {'feed': 'changes'}
    backward_params = {'feed': 'changes', 'descending': '1'}
    if extra:
        [x.update(extra) for x in [forward_params, backward_params]]
    r = backward.get_tenders(backward_params)
    if backward.session.cookies != cookie:
        raise LBMismatchError
    backward_params['offset'] = r['next_page']['offset']
    forward_params['offset'] = r['prev_page']['offset']
    queue.put(filter(callback, r['data']))
    return forward_params, backward_params


def fetch_tenders(client, src, dest):
    logger.info('Starting downloading tenders')
    while True:
        for feed in src:
            logger.info('Uploading {} tenders'.format(len(feed)))
            resp = client.fetch(feed)
            if resp:
                logger.info('fetched {} tenders'.format(len(resp)))
            dest.put(resp)
            gevent.sleep(0.5)
        gevent.sleep(1)


def create_releases(src, dest, prefix):
        logger.info('Starting generating releases')
        while True:
            for batch in src:
                logger.info('Got {} tenders'.format(len(batch)))
                for tender in batch:
                    try:
                        release = get_release_from_tender(tender, prefix)
                        logger.info("generated release for tender "
                                    "{}".format(tender['id']))
                        dest.put(release)
                    except Exception as e:
                        logger.fatal('Error {} during'
                                     ' generation release'.format(e))
                gevent.sleep(0.5)
            gevent.sleep(2)


def save(storage, src):
    logger.info('Start saving')
    while True:
        for item in src:
            if item['id'] not in storage:
                storage.save(item)
            else:
                doc = storage.get(item['id'])
                doc.update(item)
                storage.save(doc)


def exists_or_modified(db, doc):
    if doc['id'] not in db:
        return True
    else:
        if db.get(doc['id'])['dateModified'] < doc['dateModified']:
            return True
    return False
    

