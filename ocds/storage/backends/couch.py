# -*- coding: utf-8 -*-
import couchdb
from couchdb.design import ViewDefinition
from .design.tenders import views as tenders_views
from .design.releases import views as releases_views
from ocds.storage.helpers import get_db_url
from ocds.export.helpers import encoder, decoder
from couchdb.json import use
from .base import Storage
from ocds.storage.errors import DocumentNotFound
from copy import deepcopy


use(decode=decoder, encode=encoder)


class CouchStorage(Storage):

    def __init__(self, config, views):
        url = get_db_url(
            config.get('username'),
            config.get('password'),
            config.get('host'),
            config.get('port'),
        )
        server = couchdb.client.Server(url)
        db_name = config.get('name')
        if db_name not in server:
            server.create(db_name)
        self.db = server[db_name]
        ViewDefinition.sync_many(self.db, views)

    def _get(self, docid):
        if docid in self.db:
            return self.db.get(docid)
        raise DocumentNotFound

    def __repr__(self):
        return "Storage : {}".format(self.name)

    def get(self, doc_id):
        return self._get(doc_id)

    def save(self, doc):
        if '_id' not in doc:
            doc['_id'] = doc['id']
        self.db.save(doc)

    def __contains__(self, key):
        return key in self.db

    def __len__(self):
        return len(self.db)

    def __delitem__(self, key):
        del self.db[key]

    def __getitem__(self, key):
        return self._get(key)

    def __setitem__(self, key, value):
        self.db[key] = value


class TendersStorage(CouchStorage):

    def __init__(self, config):
        super(TendersStorage, self).__init__(config, tenders_views)

    def __iter__(self):
        same = []
        for i, row in enumerate(self.db.iterview('tenders/docs', 100)):
            same.append(row['value'])
            if i == 0:
                prev = row['key']
            elif prev != row['key']:
                temp = deepcopy(same)
                same = same[-1:]
                prev = row['key']
                yield temp[:-1]
        yield same

    def get_tenders_between_dates(self, datestart, datefinish):
        for row in self.db.iterview('tenders/dates',
                                    100,
                                    startkey=datestart,
                                    endkey=datefinish):
            yield row['value']


class ReleasesStorage(CouchStorage):

    def __init__(self, config):
        super(ReleasesStorage, self).__init__(config, releases_views)

    def __iter__(self):
        for row in self.db.iterview('releases/docs', 100):
            yield row['value']

    def get_by_ocid(self, key):
        for row in self.db.iterview('releases/ocid', 100, key=key):
            yield row['value']

    def get_doc(self, docid):
        if docid in self.db:
            return self.db.get(docid)

    def get_finished_ocids(self):
        same = []
        for i, row in enumerate(self.db.iterview('releases/finished', 100)):
            same.append(row['value'])
            if i == 0:
                prev = row['key']
            elif prev != row['key']:
                temp = deepcopy(same)
                same = same[-1:]
                prev = row['key']
                yield temp[:-1]
        yield same

    def save(self, doc):
        self.db.save(doc)
