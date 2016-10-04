# -*- coding: utf-8 -*-
import couchdb
from couchdb.design import ViewDefinition
from .design.tenders import views as tenders_views
from ocds.storage.helpers import get_db_url
from ocds.export.helpers import encoder, decoder
from couchdb.json import use
from .base import Storage
from ocds.storage.errors import DocumentNotFound


use(decode=decoder, encode=encoder)


class CouchStorage(Storage):

    def __init__(self, config):
        url = get_db_url(
            config.get('username'),
            config.get('password'),
            config.get('host'),
            config.get('port'),
        )
        self.server = couchdb.client.Server(url)

    def _init(self):
        if self.db_name not in self.server:
            self.server.create(self.db_name)
        self.db = self.server[self.db_name]
        ViewDefinition.sync_many(self.db, tenders_views)

    def _get(self, docid):
        if docid in self.db:
            return self.db.get(docid)
        raise DocumentNotFound

    def __repr__(self):
        return "Storage : {}".format(self.name)

    @property
    def name(self):
        return self.db_name

    @name.setter
    def name(self, name):
        self.db_name = name
        self._init()

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

    def __iter__(self):
        for row in self.db.iterview('tenders/docs', 100):
            yield row['value']
