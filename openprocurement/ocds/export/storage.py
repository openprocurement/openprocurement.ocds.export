# -*- coding: utf-8 -*-
from couchdb import Database, http
from couchdb.design import ViewDefinition


tenders_map = u"""
function(doc) {
    if(doc.status.indexOf('draft') !== -1) {return;};
    if(doc.status.indexOf('terminated') !== -1) {return;};
    if((doc.doc_type || "" ) !== 'Tender') {return;}
    if((doc.title || "" ).search("ТЕСТУВАННЯ") !== -1) {return;}
    if((doc.title_ru || "" ).search("ТЕСТИРОВАНИЕ") !== -1) {return;}
    if((doc.title_en || "" ).search("TESTING") !== -1) {return;}
    if((doc.mode || "") === 'test') {return;};
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

get_contracts_by_tender_id = ViewDefinition(
    'contracts', 'get_by_tender_id',
    map_fun=u"""function(doc) {
    if((doc.doc_type || "" ) !== 'Contract') {return;}
    if((doc.title || "" ).search("ТЕСТУВАННЯ") !== -1) {return;}
    if((doc.title_ru || "" ).search("ТЕСТИРОВАНИЕ") !== -1) {return;}
    if((doc.title_en || "" ).search("TESTING") !== -1) {return;}
    if((doc.mode || "") === 'test') {return;};
    emit(doc.tender_id, doc.id);
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
        ViewDefinition.sync_many(self, [tenders_all,
                                        tenders_date_modified,
                                        tenders_date_modified_for_package])

    def get_tender(self, contracts=False):
        for item in self.iterview('tenders/all',
                                  1000,
                                  include_docs=True,
                                  ):
            tender = item.doc
            if contracts and contracts.get_contracts_by_ten_id(tender['id']):
                tender['contracts'] = contracts.get_contracts_by_ten_id(tender['id'])
                yield tender
            else:
                yield tender


    def get_max_date(self):
        return next(iter(
            self.view('tenders/by_dateModified_pack',
                      limit=1,
                      descending=True).rows
        )).get('key')

    def get_between_dates(self, sdate, edate):
        for item in self.iterview('tenders/by_dateModified_pack',
                                  1000,
                                  startkey=sdate,
                                  endkey=edate,
                                  include_docs=True):
            yield item.doc

    def get_list_of_historical_tenders(self):
        same_ids = {}
        import pdb
        pdb.set_trace()
        prev_id = next(iter(
            self.view('tenders/all',
                      limit=1).rows
        )).get('key').split('-')[0]
        for item in self.iterview('tenders/all',
                                  1000,
                                  include_docs=True,
                                  ):
            if prev_id == item.id.split('-')[0]:
                same_ids[item.id] = item.doc
            else:
                cp = deepcopy(same_ids)
                same_ids = {}
                yield cp

class ContractsStorage(Database):

    def __init__(self, db_url, name=None):
        url = "{}/{}".format(db_url, name)
        get_or_create(db_url, name)
        super(ContractsStorage, self).__init__(url=url)
        ViewDefinition.sync_many(self, [get_contracts_by_tender_id])

    def get_contracts_by_ten_id(self, tender_id):
        return [item.doc for item in self.view('contracts/get_by_tender_id',
                                               key=tender_id,
                                               include_docs=True)
                                               if item.doc.get('status') != 'merged']
