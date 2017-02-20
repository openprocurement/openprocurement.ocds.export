# -*- coding: utf-8 -*-
from couchdb import Database, http
from couchdb.design import ViewDefinition


rel_red = """
function(key, values, rereduce) {
    var result = result || [];
    result.push.apply(result, values);
    return result;
}
"""

tenders_map = """
function(doc) {
    if(doc.status.indexOf('draft') !== -1) {return;};
    if(doc.status.indexOf('terminated') !== -1) {return;};
    if(('doc_type' in doc) && (doc.doc_type !== 'Tender')) {return;};
    if(doc.title.search("ТЕСТУВАННЯ") !== -1) {return;};
    emit(doc._id, null);
}
"""

releases_ocid = ViewDefinition(
    'releases', 'ocid',
    map_fun="""function(doc) {emit(doc.ocid, doc._id);}""",
    reduce_fun=rel_red
)

releases_all = ViewDefinition(
    'releases', 'all',
    map_fun="""function(doc) {emit(doc._id, doc.date);}"""
)

releases_tag = ViewDefinition(
    'releases', 'tag',
    map_fun="""function(doc) {emit(doc._id, doc.tag);}"""
)


tenders_all = ViewDefinition(
    'tenders', 'all',
    map_fun=tenders_map
)


tenders_date_modified = ViewDefinition(
    'tenders', 'by_dateModified',
    map_fun="""function(doc) {emit(doc.id, doc.dateModified);}"""
)

tenders_date_modified_for_package = ViewDefinition(
    'tenders', 'by_dateModified_pack',
    map_fun="""function(doc) {emit(doc.dateModified, doc.id);}"""
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
        ViewDefinition.sync_many(self, [tenders_all, tenders_date_modified, tenders_date_modified_for_package])

    def __iter__(self):
        for item in self.iterview('tenders/all', 1000, include_docs=True):
            yield item.doc

    def get_max_date(self):
        for item in self.iterview('tenders/by_dateModified', 1000):
            yield item['value']

    def get_between_dates(self, sdate, edate):
        for item in self.iterview('tenders/by_dateModified_pack', 1000,
                                 startkey=sdate, endkey=edate, include_docs=True):
            yield item.doc


class ReleasesStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name or 'releases')
        get_or_create(db_url, name)
        super(ReleasesStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [releases_ocid,
                                        releases_all,
                                        releases_tag])

    def ocid_list(self, ocid):
        for row in self.iterview('releases/ocid', 1000, key=ocid):
            yield row['value']

    def __iter__(self):
        for item in self.iterview('releases/all', 1000):
            yield item['value']
