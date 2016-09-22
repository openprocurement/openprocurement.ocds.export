import pytest
import os
import os.path
import shutil
import functools
from copy import copy
from ocds.storage import FSStorage
from ocds.storage.errors import InvalidPath


base = os.path.dirname(__file__)
path = os.path.join(base, 'test')
test_data = {
    "date": "2016-09-28T14:57:14.846483+03:00",
    "id": "0009417e6dd1413585426be68bf6a4dd",
    "test": "test"
}

@pytest.fixture(scope='function')
def temp_dir(request):
    os.makedirs(path)
    def tear_down():
        shutil.rmtree(path)
    request.addfinalizer(tear_down)


def test_create():
    assert not os.path.exists(path)
    storage = FSStorage(path)
    assert os.path.exists
    shutil.rmtree(path)


def test_save(temp_dir):
    storage = FSStorage(path)
    storage.save(test_data)
    assert os.path.exists(os.path.join(path, '2016-09-28/14/57/14/0009417e6dd1413585426be68bf6a4dd.json'))
    assert os.path.isfile(os.path.join(path, '2016-09-28/14/57/14/0009417e6dd1413585426be68bf6a4dd.json'))


def test_load(temp_dir):
    storage = FSStorage(path)
    storage.save(test_data)
    loaded = storage.get(test_data['id'])
    assert loaded['date'] == test_data['date']
    assert loaded['id'] == test_data['id']
    assert loaded['test'] == test_data['test']


def test_contains(temp_dir):
    storage = FSStorage(path)
    storage.save(test_data)
    assert "0009417e6dd1413585426be68bf6a4dd" in storage
    assert "fake" not in storage


def test_iter(temp_dir):
    storage = FSStorage(path)
    storage.save(test_data)
    for item in storage:
        assert item == test_data
