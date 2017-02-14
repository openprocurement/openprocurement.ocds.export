# -*- coding: utf-8 -*-

import jsonpatch
import logging
import ocdsmerge
import yaml
import os
from iso8601 import parse_date
from datetime import datetime
from collections import Counter
from copy import deepcopy
from .exceptions import LBMismatchError


logger = logging.getLogger(__name__)


with open(os.path.join(os.path.dirname(__file__), 'unit_codes.yaml'), 'r') as stream:
    units = yaml.load(stream)


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


def unique_tenderers(bids):
    """leave only unique tenderers as required by standard"""
    if not bids:
        return
    tenderers = [tenderer for bid in bids for tenderer in bid.get('tenderers', [])]
    return {t['identifier']['id']: t for t in tenderers}.values() if tenderers else []


def unique_documents(documents, extension=False):
    """adds `-<number>` to docs with same ids"""
    if not documents:
        return
    if extension:
        for doc in documents:
            if 'documentOf' in doc:
                doc['documentScope'] = doc.pop('documentOf')
    cout = Counter(doc['id'] for doc in documents)
    for i in [i for i, c in cout.iteritems() if c > 1]:
        for index, d in enumerate([d for d in documents if d['id'] == i]):
            d['id'] = d['id'] + '-{}'.format(index)
    return documents


def convert_cancellation(tender):
    cancellations = tender.get('cancellations')
    if cancellations:
        for cancellation in cancellations:
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


def convert_questions(tender):
    questions = tender.get('questions')
    if not questions:
        return
    for question in questions:
        if question['questionOf'] == 'lot':
            question['relatedLot'] = question['relatedItem']
            del question['relatedItem']
    return questions


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


def convert_bids(bids):
    if not bids:
        return
    new = []
    for bid in bids:
        if 'lotValues' in bid:
            for lotval in bid['lotValues']:
                bid['relatedLot'] = lotval['relatedLot']
                bid['value'] = lotval.get('value')
                new.append(bid)
        else:
            new.append(bid)
    return new


def convert_unit_and_location(items):
    if not items:
        return
    new = []
    for item in items:
        new_loc = {}
        if 'unit' in item:
            unit_code = item['unit'].get('code')
            if units.get(unit_code):
                item['unit'] = units[unit_code]
                item['unit']['scheme'] = "UNCEFACT"
                item['unit']['id'] = unit_code
            elif item['unit'].get('id'):
                pass
            else:
                item['unit']['id'] = unit_code
        if 'deliveryLocation' in item:
            if item['deliveryLocation'].get('latitude'):
                new_loc = {'geometry': {'coordinates': item['deliveryLocation'].values()}}
                item['deliveryLocation'] = new_loc
            elif 'geometry' in item['deliveryLocation']:
                pass
            else:
                del item['deliveryLocation']
        new.append(item)
    return new


def create_auction(tender):
    auctions = []
    auction = {}
    lots = tender.get('lots', [])
    for lot in lots:
        auction['url'] = lot.get('auctionUrl')
        auction['minimalStep'] = lot.get('minimalStep')
        auction['period'] = lot.get('auctionPeriod')
        auction['relatedLot'] = lot.get('id')
        auctions.append(auction)
        auction = {}
    else:
        auction['url'] = tender.get('auctionUrl')
        auction['minimalStep'] = tender.get('minimalStep')
        auction['period'] = tender.get('auctionPeriod')
    if any(auction.values()):
        auctions.append(auction)
        return auctions
    return auctions


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
