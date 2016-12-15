from couchdb import Database
from couchdb.design import ViewDefinition
from .models import ReleaseDocument

_RELEASES_OCID = ViewDefinition('releases', 'ocid', map_fun="function(doc) { emit(doc.ocid, doc.id); }", reduce_fun="function(key, values, rereduce) { var k = key[0][0]; var result = result || {}; result[k] = result[k] || []; result[k].push(values); return result; }")
_RELEASES_ALL = ViewDefinition('releases', 'all', map_fun="function(doc) { emit(doc.id, doc); }")


class ReleasesStorage(Database):

    def __init__(self, db_url, name=None):
        super(ReleasesStorage, self).__init__(db_url, name=name or 'releases')
        ViewDefinition.sync_many(self, [_RELEASES_OCID, _RELEASES_ALL])

    def ocid_list(self, ocid):
        for row in self.iterview('releases/ocid', 1000, key=ocid):
            yield row['value']
