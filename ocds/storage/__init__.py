from couchdb import Database
from couchdb.design import ViewDefinition
from .models import Release


_releases_ocid = ViewDefinition('releases', 'ocid', map_fun="function(doc) { emit(doc.ocid, doc.id); }", reduce_fun="function(key, values, rereduce) { var k = key[0][0]; var result = result || {}; result[k] = result[k] || []; result[k].push(values); return result; }")
_releases_all = ViewDefinition('releases', 'all', map_fun="function(doc) { emit(doc.id, doc); }")
_tenders_all = ViewDefinition('tenders', 'all', map_fun="function(doc) { emit(doc.id, doc); }")


class TendersStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name)
        super(TendersStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [_tenders_all])


class ReleasesStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name)
        super(ReleasesStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [_releases_ocid, _releases_all])

    def ocid_list(self, ocid):
        for row in self.iterview('releases/ocid', 1000, key=ocid):
            yield row['value']
