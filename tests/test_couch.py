import pytest
import couchdb
from ocds.storage import TendersStorage
from ocds.storage.errors import DocumentNotFound

CONFIG = {
    "username": "",
    "password": "",
    "host": "127.0.0.1",
    "port": "5984",
    "name": "test"
}
DB = 'test'
SERVER = couchdb.Server("http://{}:{}".format(CONFIG['host'], CONFIG['port']))
test_data = {
    "date": "2016-09-28t14:57:14.846483+03:00",
    "id": "0009417e6dd1413585426be68bf6a4dd",
    "test": "test",
    "dateModified": "2016-09-28t14:57:14.846483+03:00",
    "tenderID": "test"
}


@pytest.fixture(scope='function')
def db(request):
    if DB not in SERVER:
        SERVER.create(DB)

    def delete():
        del SERVER[DB]

    request.addfinalizer(delete)


def test_create():
    assert DB not in SERVER
    storage = TendersStorage(CONFIG)
    assert DB in SERVER
    del SERVER[DB]


def test_save(db):
    storage = TendersStorage(CONFIG)
    storage.save(test_data)
    assert test_data['id'] in SERVER[DB]
    doc = SERVER[DB].get(test_data['id'])
    assert doc['_id'] == test_data['id']
    assert doc['date'] == test_data['date']
    assert doc['test'] == test_data['test']


def test_load(db):
    storage = TendersStorage(CONFIG)
    storage.save(test_data)
    loaded = storage.get(test_data['id'])
    assert loaded['date'] == test_data['date']
    assert loaded['id'] == test_data['id']
    assert loaded['test'] == test_data['test']
    with pytest.raises(DocumentNotFound):
        loaded = storage.get('Invalid')


def test_contains(db):
    storage = TendersStorage(CONFIG)
    storage.save(test_data)
    assert "0009417e6dd1413585426be68bf6a4dd" in storage
    assert "fake" not in storage


def test_iter(db):
    storage = TendersStorage(CONFIG)
    storage.save(test_data)
    for item in storage:
        assert item[0] == test_data


def test_count(db):
    storage = TendersStorage(CONFIG)
    storage.save(test_data)
    assert len(storage) == 2


def test_remove(db):
    storage = TendersStorage(CONFIG)
    storage.save(test_data)
    assert test_data['id'] in storage
    del storage[test_data['id']]
    assert not test_data['id'] in storage


def test_get_set(db):
    storage = TendersStorage(CONFIG)
    storage.save(test_data)
    storage[test_data['id']] = test_data
    assert test_data['id'] in storage
    assert test_data == storage[test_data['id']]
