import itertools
from couchdb import Database
from uuid import uuid4
from couchdb.design import ViewDefinition
from .models import Release
from openprocurement.ocds.export import Tender, get_ocid, Release
from couchdb_schematics.document import Document


_releases_ocid = ViewDefinition('releases', 'ocid', map_fun="function(doc) { emit(doc.ocid, doc._id); }", reduce_fun="function(key, values, rereduce) { var k = key[0][0]; var result = result || {}; result[k] = result[k] || []; result[k].push(values); return result; }")
_releases_all = ViewDefinition('releases', 'all', map_fun="function(doc) { emit(doc._id, doc); }")
_releases_tag = ViewDefinition('releases', 'tag', map_fun="function(doc) { emit(doc._id, doc.tag); }")
_tenders_all = ViewDefinition('tenders', 'all', map_fun="function(doc) { if(doc.doc_type !== 'Tender') {return;}; if(doc.status.indexOf('draft') !== -1) {return;}; emit(doc._id, doc); }")
_tenders_dateModified = ViewDefinition('tenders', 'byDateModified', map_fun="function(doc) { if(doc.doc_type !== 'Tender') {return;}; emit(doc.dateModified, doc); }")


class Release(Document, Release):
   pass


class TendersStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name)
        super(TendersStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [_tenders_all, _tenders_dateModified])

    def __iter__(self):
        for item in self.iterview('tenders/all', 1000):
            yield item['value']


class ReleasesStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name or 'releases')
        super(ReleasesStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [_releases_ocid, _releases_all, _releases_tag])

    def ocid_list(self, ocid):
        for row in self.iterview('releases/ocid', 1000, key=ocid):
            yield row['value']

    def __iter__(self):
        for item in self.iterview('releases/all', 1000):
            yield item['value']


def clean_up(data):
    if 'amendment' in data:
        del data['amendment']
    return data


def release_tenders(tenders, prefix):
    """ returns list of Release object created from `tenders` with amendment info and ocid `prefix` """
    prev_tender = next(tenders)
    for tender in tenders:
        data = {}
        for field in ['tender', 'awards', 'contracts']:
            model = getattr(Release, field).model_class
            if field in tender:
                collection_prev = prev_tender.get(field, [])
                collection_new = tender.get(field, [])
                collection = []
                for a, b in itertools.izip_longest(collection_prev, collection_new, fillvalue={}):
                    obj = model.fromDiff(clean_up(b), clean_up(a))
                    if obj:
                        collection.append(obj)
                if collection:
                    data[field] = collection
            elif field == 'tender':
                rel = model.fromDiff(clean_up(prev_tender), clean_up(tender))
                if rel:
                    data['tender'] = rel
        if data:

            data['ocid'] = get_ocid(prefix, tender['tenderID'])
            data['_id'] = uuid4().hex
            if data:
                yield Release(data)
        prev_tender = tender


def release_tender(tender, prefix):
    ocid = get_ocid(prefix, tender['tenderID'])
    return Release(dict(tender=tender, ocid=ocid, **tender))
