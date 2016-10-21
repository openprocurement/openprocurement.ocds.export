# -*- coding: utf-8 -*-
import iso8601
import json
from datetime import datetime
from .tag import Tag
from uuid import uuid4
import ocdsmerge


def get_ocid(prefix, tenderID):
    return "{}-{}".format(prefix, tenderID)


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


def get_tag(tags):
    t = []
    for tag in tags:
        if isinstance(tag, (list, tuple)):
            if tag[0].__tag__ == "awards":
                t.append('award')
            elif tag[0].__tag__ == "contracts":
                t.append('contract')
        else:
            if tag.__tag__ == 'tender':
                t.append(tag.__tag__)
    return t


def encoder(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    return json.dumps(obj)


def decoder(obj):
    return json.loads(obj)


def check_releases(releases):
    statuses = ['complete', 'unsuccesful', 'cancelled']
    for _rel in releases:
        if _rel['tender']['status'] in statuses:
            return True
            break


def get_compiled_release(releases):
    return ocdsmerge.merge(releases)


def generate_uri():
    return 'https://fake-url/tenders-{}'.format(uuid4().hex)
