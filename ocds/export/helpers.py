# -*- coding: utf-8 -*-
import itertools
import iso8601
import json
from datetime import datetime
from .tag import Tag
from uuid import uuid4


DEFAULTS = {
    'publisher': {
        'name': 'ДП Прозорро',
    },
    'licence': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'publicationPolicy': 'https://prozorro.gov.ua/publication-policy',
    'ocid_prefix': 'ocds-xxxxxx'
}


def parse_tender(tender):

    if 'bids' in tender:
        tender['tenderers'] = list(itertools.chain.from_iterable(
            map(lambda b: b.get('tenderers', ''), tender['bids'])))

        tender['numberOfTenderers'] = len(tender['tenderers'])
        del tender['numberOfBids']
        del tender['bids']

    if 'submissionMethod' in tender:
        tender['submissionMethod'] = [tender['submissionMethod']]
    if 'minimalStep' in tender:
        tender['minValue'] = tender['minimalStep']
        del tender['minimalStep']
    if 'awards' in tender:
        tender = parse_award(tender)
    return tender


def get_ocid(prefix, tenderID):
    return "{}-{}".format(prefix, tenderID)


def parse_award(tender):
    if 'lots' in tender:
        for award in tender['awards']:
            award['items'] = [item for item in tender['items']
                              if item['relatedLot'] == award['lotID']]
    else:
        for award in tender['awards']:
            award['items'] = tender['items']
    return tender


def now():
    return iso8601.parse_date(datetime.now().isoformat())


def get_field(tender, field):
    if field == 'buyer':
        return tender['procuringEntity']
    if field in tender:
        return tender[field]
    return []


def get_tags_from_tender(tender):

    def get_tag(vals, tag):
        if isinstance(vals, list):
            return [Tag(tag, v) for v in vals]
        else:
            return Tag(tag, vals)

    fields = ['awards', 'contracts', 'buyer']

    return [x for x in
            map(lambda t: get_tag(get_field(tender, t), t), fields) if x]


def generate_id():
    return uuid4().hex


def get_tag(tags):
    t = []
    for tag in tags:
        if isinstance(tag, (list, tuple)):
            t.append(tag[0].__tag__)
        else:
            t.append(tag.__tag__)
    return t


def encoder(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    return json.dumps(obj)


def decoder(obj):
    return json.loads(obj)