# -*- coding: utf-8 -*-
import itertools
import iso8601
import simplejson as json
import ocdsmerge
import jsonpatch as jpatch
from datetime import datetime
from collections import Counter
from uuid import uuid4
from copy import deepcopy


def tender_converter(tender):

    if 'bids' in tender:
        tender['tenderers'] = list(itertools.chain.from_iterable(
            map(lambda b: b.get('tenderers', ''), tender['bids'])))

        del tender['numberOfBids']
        del tender['bids']

    if 'minimalStep' in tender:
        tender['minValue'] = tender['minimalStep']
        del tender['minimalStep']
    if 'awards' in tender:
        tender = parse_award(tender)
    return tender


def unique_tenderers(tenderers):
    tenderers = [{t['identifier']['id']: t} for t in tenderers]
    if tenderers:
        res = [t.values() for t in tenderers][0]
        return res
    return []


def unique_documents(documents):
    cout = Counter(doc['id'] for doc in documents)
    for i in [i for i, c in cout.iteritems() if c > 1]:
        for index, d in enumerate([d for d in documents if d['id'] == i]):
            d['id'] = d['id'] + '-{}'.format(index)
   

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
    tags = [x for x in
            map(lambda t: get_tag(get_field(tender, t), t), fields) if x]
    tags.append(Tag('tender', tender))
    return tags


def generate_id():
    return uuid4().hex


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


def make_tags(patch):
    tags = set()
    for op in patch:
        name = op['path'].split('/')
        if name[1] in ['awards', 'contracts']:
            try:
                int(name[2])
                if len(name) == 3:
                    tags.add(name[1][:-1])
                elif name[3] == 'status' and op['value'] == 'cancelled':
                    tags.add('{}Cancellation'.format(name[1][:-1]))
                else:
                    tags.add("{}Update".format(name[1][:-1]))
            except Exception:
                tags.add("{}Update".format(name[1][:-1]))
                pass
        else:
            tags.add("tenderUpdate")
    return tags


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
    return 'ТЕСТУВАННЯ'.decode('utf-8') not in tender['title']
   

def release_tender(tender, prefix):
    date = tender['dateModified']
    tags = get_tags_from_tender(parse_tender(tender))
    return Release(
        get_ocid(prefix, tender['tenderID']),
        tags,
        date
    )


def release_tenders(tenders, prefix):
    prev_tender = next(tenders)
    first_rel = release_tender(prev_tender, prefix)
    first_rel['tag'] = ['tender']
    yield first_rel
    for tender in tenders:
        patch = jpatch.make_patch(prev_tender, tender)
        release = release_tender(tender, prefix)
        release['tag'] = list(make_tags(patch))
        prev_tender = tender
        yield release
