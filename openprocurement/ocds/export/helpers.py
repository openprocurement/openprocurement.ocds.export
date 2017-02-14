# -*- coding: utf-8 -*-

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
