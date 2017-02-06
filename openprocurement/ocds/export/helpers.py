# -*- coding: utf-8 -*-
import yaml
import itertools
import simplejson as json
import jsonpatch as jpatch
import gevent
import logging
import os.path
import json
from requests.exceptions import HTTPError
from iso8601 import parse_date
from datetime import datetime
from collections import Counter
from uuid import uuid4
from copy import deepcopy
from .exceptions import LBMismatchError


logger = logging.getLogger(__name__)


def now():
    # uri = StringType()
    return parse_date(datetime.now().isoformat()).isoformat()


def generate_uri():
    return 'https://fake-url/tenders-{}'.format(uuid4().hex)


def get_ocid(prefix, tenderID):
    """greates unique contracting identifier"""
    return "{}-{}".format(prefix, tenderID)


def read_unit():
    with open('/data/dimon.obert/ocds/openprocurement.ocds.export/var/unit_codes/en.yaml', 'r') as stream:
        return yaml.load(stream)


def tender_converter(tender):
    """ converts raw openprocurement data into acceptable by OCDS standard """
    if 'id' in tender:
        tender['_id'] = tender['id']
    if 'auctions' in tender or not tender:
        return tender
    awards = tender.get('awards')
    contracts = tender.get('contracts')
    bids = tender.get('bids')
    if bids:
        tender['bids'] = convert_bids(bids)
    if 'items' in tender:
        tender['items'] = [convert_unit_and_location(item) for item in tender['items'] if 'items' in tender]
    if awards:
        for award in awards:
            if 'items' in award:
                award['items'] = [convert_unit_and_location(item) for item in award['items'] if 'items' in award]
    if contracts:
        for contract in contracts:
            if 'items' in contract:
                contract['items'] = [convert_unit_and_location(item) for item in contract['items'] if 'items' in contract]
    if 'cancellations' in tender:
        tender = convert_cancellation(tender)
    tender = convert_status(tender)
    tender['auctions'] = create_auction(tender)
    return tender


def convert_status(tender):
    if '.' in tender['status']:
        tender['currentStage'] = tender['status']
    return tender


def create_auction(tender):
    auctions = []
    auction = {}
    fields = ['auctionUrl', 'minimalStep', 'auctionPeriod']
    lots = tender.get('lots', [])
    for lot in lots:
        auction = {field: lot.get(field) for field in fields}
        auction['relatedLot'] = lot['id']
        auction['auctionOf'] = 'lot'
        auctions.append(auction)
        auction = {}
    auction = {field: tender.get(field) for field in fields}
    if any(auction.values()):
        auction['auctionOf'] = 'tender'
        auctions.append(auction)
        return auctions
    return auctions


def convert_unit_and_location(item):
    try:
        unit_code = item['unit']['code']
        item['unit'] = read_unit()[unit_code]
        item['unit']['code'] = unit_code
    except KeyError:
        pass
    if 'deliveryLocation' in item:
        if item['deliveryLocation']['latitude']:
            item['deliveryLocation']['coordinates'] = item['deliveryLocation'].values()
    return item


def convert_bids(bids):
    new = []
    for bid in bids:
        if 'lotValues' in bid:
            for lotval in bid['lotValues']:
                bid['relatedLot'] = lotval['relatedLot']
                bid['value'] = lotval['value']
                new.append(bid)
        else:
            new.append(bid)
    return new


def convert_cancellation(tender):
    for cancellation in tender['cancellations']:
        if cancellation['cancellationOf'] == 'tender':
            tender['pendingCancellation'] = True
        if 'documents' in cancellation:
            for document in cancellation['documents']:
                document['documentType'] = 'tenderCancellation'
                documents = tender.get('documents', [])
                documents.append(document)
            tender['documents'] = documents
        elif cancellation['cancellationOf'] == 'lot':
            for lot in tender['lots']:
                if lot['id'] == cancellation['relatedLot']:
                    lot['pendingCancellation'] = True
            if 'documents' in cancellation:
                for document in cancellation['documents']:
                    document['documentType'] = 'lotCancellation'
                    documents = tender.get('documents', [])
                    documents.append(document)
                tender['documents'] = documents
    return tender


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


def patch_converter(patch):
    """creates OCDS Amendment dict"""
    return [{'property': op['path'], 'former_value': op.get('value')} for op in patch]


def award_converter(tender):
    if 'lots' in tender:
        for award in tender['awards']:
            award['items'] = [item for item in tender['items']
                              if item['relatedLot'] == award['lotID']]
    else:
        for award in tender['awards']:
            award['items'] = tender['items']
    return tender


def encoder(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    return json.dumps(obj)


def decoder(obj):
    return json.loads(obj)


def add_revisions(tenders):
    prev_tender = tenders[0]
    new_tenders = []
    for tender in tenders[1:]:
        patch = jpatch.make_patch(prev_tender, tender)
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
                version, tender = client.get_tender(_id)
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
        patch = [p for p in jpatch.make_patch(doc, tender).patch if not p['path'].startswith('/_rev')]
        revisions.append(patch)
        doc.update(tender)
        doc['revisions'] = revisions
        storage.save(doc)
