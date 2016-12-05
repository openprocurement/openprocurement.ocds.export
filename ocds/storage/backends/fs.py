import os
import os.path
import logging
import simplejson as json
from .base import Storage
from ocds.export.helpers import encoder
from ocds.storage.errors import InvalidPath, DocumentNotFound


join = os.path.join


logger = logging.getLogger(__name__)


class FSStorage(Storage):

    def __init__(self, base_path, builder):
        self.base_path = base_path
        self._builder = builder
        if not os.path.exists(self.base_path):
            logger.warn('Initial path not exists. Creating')
            try:
                os.makedirs(self.base_path)
            except (IOError, OSError) as e:
                logger.error("Couldn't create destination dir."
                             "Error {}".format(e))
                raise InvalidPath('No destination folder')

    def _walk(self):
        for path, _, files in os.walk(self.base_path):
            for f in files:
                yield join(path, f)

    def __repr__(self):
        return "Storage on: {}".format(self.base_path)

    def __delitem__(self, key):
        if not self._check(key):
            raise DocumentNotFound
        os.remove(key)
        return True

    def _check(self, key):
        return os.path.exists(key)

    def __getitem__(self, key):
        if not self._check(key):
            raise DocumentNotFound
        return self._load(key)

    def __setitem__(self, key, value):
        self._write(value)

    def __len__(self):
        return sum((1 for _ in self._walk()))

    def _name(self, obj):
        return '{}.json'.format(obj['id'])

    def _write(self, obj):
        path = self._builder(self.base_path, obj)
        if not os.path.exists(path):
            os.makedirs(path)
        name = self._name(obj)
        file_path = join(path, name)
        with open(file_path, 'w') as out:
            out.write(encoder(obj))

    def _load(self, key):
        with open(key) as out:
            result = json.load(out)
        return result

    def _find(self, json_id):
        name = '{}.json'.format(json_id)
        for cur_dir, _, files in os.walk(self.base_path):
            if name in files:
                return join(cur_dir, name)
        return False

    def __contains__(self, key):
        return self._find(key)

    def __iter__(self):
        for f in self._walk():
            with open(f) as json_file:
                ff = json.load(json_file)
            yield ff

    def save(self, obj):
        self._write(obj)

    def get(self, key):
        path = self._find(key)
        if path:
            return self._load(path)
        raise DocumentNotFound

    def read_by_full_path(self, release):
        path = os.path.join(self.base_path, release['path'], release['_id']) + '.json'
        return self._load(path)
