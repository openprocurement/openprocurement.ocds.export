# -*- coding: utf-8 -*-
import itertools
import simplejson as json
import ocdsmerge
import jsonpatch as jpatch
from iso8601 import parse_date
from datetime import datetime
from collections import Counter
from uuid import uuid4
from copy import deepcopy


def tender_converter(tender):
    """ converts raw openprocurement data into acceptable by OCDS standard """
    if 'bids' in tender:
        tender['tenderers'] = list(itertools.chain.from_iterable(
            map(lambda b: b.get('tenderers', ''), tender['bids'])))

        del tender['numberOfBids']
        del tender['bids']
    elif 'tenderers' not in tender:
        tender['tenderers'] = []
    tender['tenderers'] = unique_tenderers(tender['tenderers'])
    if 'id' in tender:
        tender['_id'] = tender['id']
        del tender['id']

    if 'minimalStep' in tender:
        tender['minValue'] = tender['minimalStep']
        del tender['minimalStep']
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


def get_ocid(prefix, tenderID):
    """greates unique contracting identifier"""
    return "{}-{}".format(prefix, tenderID)


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


def get_compiled_release(releases):
    compiled = ocdsmerge.merge(releases)
    if 'bids' in compiled['tender'].keys():
        for bid in compiled['tender']['bids']:
            if 'lotValues' in bid.keys():
                for lotval in bid['lotValues']:
                    del lotval['id']
    return compiled


def generate_uri():
    return 'https://fake-url/tenders-{}'.format(uuid4().hex)


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
    return 'ТЕСТУВАННЯ'.decode('utf-8') not in tender['title']


def now():
    # uri = StringType()
    return parse_date(datetime.now().isoformat()).isoformat()
