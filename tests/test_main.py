# -*- coding: utf-8 -*-
import pytest
import couchdb
from ocds.storage import TendersStorage, ReleasesStorage, MainStorage
from ocds.storage.errors import DocumentNotFound
import os
import shutil
from copy import deepcopy


base = os.path.dirname(__file__)
path = os.path.join(base, 'test')
CONFIG = {
    "releases_db": {
        "username": "",
        "password": "",
        "host": "127.0.0.1",
        "port": 5984,
        "name": "test_releases"
    },
    "tenders_db": {
        "username": "",
        "password": "",
        "host": "127.0.0.1",
        "port": 5984,
        "name": "test_tenders"
    },
    "release": {
        "publisher": {
            "name": "test"
        },
        "license": "test",
        "initiationType": "test",
        "publicationPolicy": "test",
        "prefix": "test"
    }
}
DB_tender = 'test_tenders'
DB_release = 'test_releases'
SERVER = couchdb.Server("http://{}:{}".format(CONFIG.get("releases_db")
                                              ['host'], CONFIG.get("tenders_db")['port']))
test_tender1 = {
    "id": "1",
    "test": "test",
    "dateModified": "2016-09-28t14:57:14.846483+03:00",
    "status": "cancelled",
    'tenderID': "test1",
    "procuringEntity": {
        "contactPoint": {
            "test": "test"
        },
        "identifier": {
            "test": "test"
        },
        "name": "test",
        "address": {
            "test": "test"
        }
    }
}


@pytest.fixture(scope='function')
def db(request):
    if DB_tender not in SERVER and DB_release not in SERVER:
        SERVER.create(DB_tender)
        SERVER.create(DB_release)
        os.makedirs(path)

    def delete():
        del SERVER[DB_tender]
        del SERVER[DB_release]
        shutil.rmtree(path)

    request.addfinalizer(delete)


def test_create():
    assert not os.path.exists(path)
    assert DB_release not in SERVER
    assert DB_tender not in SERVER
    mainst = MainStorage(CONFIG, path)
    assert DB_release in SERVER
    assert DB_tender in SERVER
    del SERVER[DB_tender]
    del SERVER[DB_release]
    shutil.rmtree(path)


def test_find(db):
    mainst = MainStorage(CONFIG, path)
    mainst.ten_storage.save(test_tender1)
    mainst.save()
    ocid = (CONFIG['release']['prefix']) + "-" + (test_tender1['tenderID'])
    assert ocid in mainst


def test_write(db):
    mainst = MainStorage(CONFIG, path)
    mainst.ten_storage.save(test_tender1)
    test_tender1['_id'] = '3'
    mainst.ten_storage.save(test_tender1)
    mainst.save()
    ocid = (CONFIG['release']['prefix']) + "-" + (test_tender1['tenderID'])
    assert mainst.rel_storage[ocid]['date'] == test_tender1['dateModified']
    test_tender1['_id'] = '4'
    test_tender1['dateModified'] = "2016-10-28t14:57:14.846483+03:00"
    mainst.ten_storage.save(test_tender1)
    mainst.save()
    assert mainst.rel_storage[ocid]['date'] == test_tender1['dateModified']
    assert len(mainst.rel_storage) == 2
    assert len(mainst.ten_storage) == 4
    assert len(mainst.fs_storage) == 2
    test_tender1['_id'] = '5'
    test_tender1['tenderID'] = "test2"
    mainst.ten_storage.save(test_tender1)
    mainst.save()
    assert mainst.rel_storage[ocid]['date'] == test_tender1['dateModified']
    assert len(mainst.rel_storage) == 3
    assert len(mainst.ten_storage) == 5
    assert len(mainst.fs_storage) == 3
    test_tender1['_id'] = '6'
    prev_date = deepcopy(test_tender1['dateModified'])
    test_tender1['dateModified'] = "2016-09-28t14:57:14.846483+03:00"
    mainst.ten_storage.save(test_tender1)
    mainst.save()
    ocid = (CONFIG['release']['prefix']) + "-" + (test_tender1['tenderID'])
    assert mainst.rel_storage[ocid]['date'] == prev_date
    assert len(mainst.rel_storage) == 3
    assert len(mainst.ten_storage) == 6
    assert len(mainst.fs_storage) == 3
