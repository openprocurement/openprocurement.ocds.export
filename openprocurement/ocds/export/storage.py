import itertools
from couchdb import Database
from uuid import uuid4
from couchdb.design import ViewDefinition
from openprocurement.ocds.export.models import Release, ReleasePackage, get_ocid, Tender
from couchdb_schematics.document import Document


_releases_ocid = ViewDefinition('releases', 'ocid', map_fun="function(doc) { emit(doc.ocid, doc._id); }", reduce_fun="function(key, values, rereduce) { var k = key[0][0]; var result = result || {}; result[k] = result[k] || []; result[k].push(values); return result; }")
_releases_all = ViewDefinition('releases', 'all', map_fun="function(doc) { emit(doc._id, doc); }")
_releases_tag = ViewDefinition('releases', 'tag', map_fun="function(doc) { emit(doc._id, doc.tag); }")
_tenders_all = ViewDefinition('tenders', 'all', map_fun="function(doc) { if(doc.doc_type !== 'Tender') {return;}; if(doc.status.indexOf('draft') !== -1) {return;}; emit(doc._id, doc); }")
_tenders_dateModified = ViewDefinition('tenders', 'byDateModified', map_fun="function(doc) { if(doc.doc_type !== 'Tender') {return;}; emit(doc.dateModified, doc); }")


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
