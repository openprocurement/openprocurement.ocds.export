import itertools
from couchdb import Database, http
from uuid import uuid4
from couchdb.design import ViewDefinition
from openprocurement.ocds.export.models import Release, ReleasePackage, get_ocid, Tender
from couchdb_schematics.document import Document


_releases_ocid = ViewDefinition('releases', 'ocid', 
    map_fun="""function(doc) { 
                 emit(doc.ocid, doc._id);
    }""",
    reduce_fun="""function(key, values, rereduce) { 
                        var result = result || [];
                        result.push.apply(result, values);
                        return result; 
    }"""
)

_releases_all = ViewDefinition('releases', 'all', 
    map_fun="""function(doc) { 
                emit(doc._id, doc); 
    }"""
)
_releases_tag = ViewDefinition('releases', 'tag', 
    map_fun="""function(doc) {
                    emit(doc._id, doc.tag); 
    }"""
)
_tenders_all = ViewDefinition('tenders', 'all', 
    map_fun="""function(doc) { 
                    if(doc.status.indexOf('draft') !== -1) {return;}; 
                    emit(doc._id, doc); 
    }"""
)
_tenders_date_modified = ViewDefinition('tenders', 'by_dateModified', 
    map_fun="""function(doc) {
                emit(doc.id, doc.dateModified);
    }"""
)

def get_or_create(url, name):
    resource = http.Resource(url, session=None)
    try:
        return resource.head(name)
    except http.ResourceNotFound:
        resource.put_json(name)



class TendersStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name)
        get_or_create(db_url, name)
        super(TendersStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [_tenders_all, _tenders_date_modified])

    def __iter__(self):
        for item in self.iterview('tenders/all', 1000):
            yield item['value']


class ReleasesStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name or 'releases')
        get_or_create(db_url, name)
        super(ReleasesStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [_releases_ocid, _releases_all, _releases_tag])

    def ocid_list(self, ocid):
        for row in self.iterview('releases/ocid', 1000, key=ocid):
            yield row['value']

    def __iter__(self):
        for item in self.iterview('releases/all', 1000):
            yield item['value']
