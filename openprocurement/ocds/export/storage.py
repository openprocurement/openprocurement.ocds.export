# -*- coding: utf-8 -*-
from couchdb import Database, http
from couchdb.design import ViewDefinition


tenders_map = u"""
function(doc) {
    if(doc.status.indexOf('draft') !== -1) {return;};
    if(doc.status.indexOf('terminated') !== -1) {return;};
    if(('doc_type' in doc) && (doc.doc_type !== 'Tender')) {return;};
    if(doc.title.search("ТЕСТУВАННЯ") !== -1) {return;};
    emit(doc._id, null);
}
"""


tenders_all = ViewDefinition(
    'tenders', 'all',
    map_fun=tenders_map
)


tenders_date_modified = ViewDefinition(
    'tenders', 'by_dateModified',
    map_fun=u"""function(doc) {emit(doc.id, doc.dateModified);}"""
)

tenders_date_modified_for_package = ViewDefinition(
    'tenders', 'by_dateModified_pack',
    map_fun=u"""function(doc) {emit(doc.dateModified, doc.id);}"""
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
        ViewDefinition.sync_many(self, [tenders_all,
                                        tenders_date_modified,
                                        tenders_date_modified_for_package])

    def __iter__(self):
        for item in self.iterview('tenders/all', 1000, include_docs=True):
            yield item.doc

    def get_max_date(self):
        for item in self.iterview('tenders/by_dateModified', 1000):
            yield item['value']

    def get_between_dates(self, sdate, edate):
        for item in self.iterview('tenders/by_dateModified_pack',
                                  1000,
                                  startkey=sdate,
                                  endkey=edate,
                                  include_docs=True):
            yield item.doc
