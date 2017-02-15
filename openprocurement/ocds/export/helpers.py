# -*- coding: utf-8 -*-

import jsonpatch
import gevent
import logging
import ocdsmerge
from requests.exceptions import HTTPError
from iso8601 import parse_date
from datetime import datetime
from collections import Counter
from copy import deepcopy
from .exceptions import LBMismatchError


logger = logging.getLogger(__name__)


def now():
    return parse_date(datetime.now().isoformat()).isoformat()


def get_ocid(prefix, tenderID):
    """greates unique contracting identifier"""
    return "{}-{}".format(prefix, tenderID)


def build_package(config):
    package = {}
    package['publishedDate'] = now()
    for k in ['publisher', 'license', 'publicationPolicy']:
        if k in config:
            package[k] = config.get(k)
    return package


def unique_tenderers(tenderers):
    """leave only unique tenderers as required by standard"""
    return {t['identifier']['id']: t for t in tenderers}.values() if tenderers else []


def unique_documents(documents):
    """adds `-<number>` to docs with same ids"""
    if not documents:
        return
    cout = Counter(doc['id'] for doc in documents)
    for i in [i for i, c in cout.iteritems() if c > 1]:
        for index, d in enumerate([d for d in documents if d['id'] == i]):
            d['id'] = d['id'] + '-{}'.format(index)


def award_converter(tender):
    if 'lots' in tender:
        for award in tender.get('awards', []):
            award['items'] = [
                item for item in tender.get('items')
                if item.get('relatedLot') == award.get('lotID')
            ]
    else:
        for award in tender.get('awards', []):
            award['items'] = tender.get('items')
    return tender.get('awards', [])


def add_revisions(tenders):
    prev_tender = tenders[0]
    new_tenders = []
    for tender in tenders[1:]:
        patch = jsonpatch.make_patch(prev_tender, tender)
        tender['revisions'] = list(patch)
        prev_tender = deepcopy(tender)
        new_tenders.append(tender)
        del prev_tender['revisions']
    return new_tenders


def mode_test(tender):
    """ drops all test mode tenders """
    return 'ТЕСТУВАННЯ'.decode('utf-8') in tender['title']


def get_start_point(forward, backward, cookie, queue,
                    callback=lambda x: x, extra={}):
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
            if not feed:
                continue
            logger.info('Uploading {} tenders'.format(len(feed)))
            resp = client.fetch(feed)
            if resp:
                logger.info('fetched {} tenders'.format(len(resp)))
                dest.put(resp)
        gevent.sleep(0.5)


def fetch_tender_versioned(client, src, dest):
    logger.info('Starting downloading tender')
    while True:
        for feed in src:
            if not feed:
                gevent.sleep(0.5)
                continue

            for _id in [i['id'] for i in feed]:
                tenders = []
                version, tender = client.get_tender(_id, version='10000')
                tender['_id'] = tender['id']
                tenders.append(tender)
                logger.info('Got tender id={}, version={}'.format(tender['id'], version))
                try:
                    while version and version not in ['1', '0']:
                        version = str(int(version) - 1)
                        logger.info('Getting prev version = {}'.format(version))
                        version, tender = client.get_tender(_id, version)
                        tenders.append(tender)
                except HTTPError:
                    logger.fatal("Falied to retreive tender id={} \n"
                                 "version {}".format(tender['id'], version))
                    continue
                dest.put(tenders)


def save_items(storage, src, dest):
    def save(obj):
        if hasattr(obj, 'store'):
            obj.store(storage)
        else:
            storage.save(obj)

    logger.info('Start saving')
    while True:
        for item in src:
            if isinstance(item, list):
                for obj in item:
                    save(obj)
                    logger.info('Saved doc {}'.format(obj['id']))
            else:
                save(item)
                logger.info('Saved doc {}'.format(item['id']))


def exists_or_modified(storage, doc):
    resp = storage.view('tenders/by_dateModified', key=doc['id'])
    try:
        date_mod = next(r['value'] for r in resp)
        return date_mod < doc.get('dateModified')
    except StopIteration:
        return True


def save_patched(storage, tender):
    if '_id' not in tender:
        tender['_id'] = tender['id']
    resp = storage.view('tenders/by_dateModified', key=tender['id'])
    try:
        date_mod = next(r['value'] for r in resp)
    except StopIteration:
        date_mod = None
    if date_mod is None:
        logger.info('savig tender id={}'.format(tender['id']))
        storage.save(tender)
        return

    if date_mod < tender['dateModified']:
        logger.info('Updated tender id={}'.format(tender['id']))
        doc = storage.get(tender['id'])
        revisions = doc.pop('revisions', [])
        patch = [p for p in jsonpatch.make_patch(doc, tender).patch if not p['path'].startswith('/_rev')]
        revisions.append(patch)
        doc.update(tender)
        doc['revisions'] = revisions
        storage.save(doc)


def compile_releases(releases, versioned=False):
    return ocdsmerge.merge(releases) if not versioned\
            else ocdsmerge.merge_versioned(releases)
