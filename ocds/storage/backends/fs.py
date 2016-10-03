import os
import os.path
import logging
import datetime
import simplejson as json
from .base import Storage
from ocds.export.helpers import encoder
from ocds.storage.errors import InvalidPath


join = os.path.join


logger = logging.getLogger(__name__)


class FSStorage(Storage):

    def __init__(self, base_path):
        self.base_path = base_path
        self.path_fmt = '%Y-%m-%d/%H/%M%/%S'
        if not os.path.exists(self.base_path):
            logger.warn('Initial path not exists. Creating')
            try:
                os.makedirs(self.base_path)
            except (IOError, OSError) as e:
                logger.error("Couldn't create destination dir."
                             "Error {}".format(e))
                raise InvalidPath('Not destination folder')

    def _walk(self):
        for path, _, files in os.walk(self.base_path):
            for f in files:
                yield join(path, f)

    def _write(self, obj):
        path = join(self.base_path,
                    self._path_from_date(obj['date']))
        file_path = join(path, '{}.json'.format(obj['id']))
        with open(file_path, 'w') as out:
            out.write(encoder(obj))

    def _load(self, key):
        with open(join(self.base_path, key)) as out:
            result = json.load(out)
        return result

    def _from_string(self, string):
        return datetime.datetime.strptime('%Y-%m-%dT%H:%M:$S')

    def _path_from_date(self, date):
        if isinstance(date, str):
            path = self._from_string(date).srtftime(self.path_fmt)
        if isinstance(date, datetime.date):
            path = date.strftime(self.path_fmt)
        return path

    def __contains__(self, key):
        try:
            fs = open(join(self.base_path, key))
            result = True
        except (IOError, OSError):
            result = False
        finally:
            fs.close()
        return result

    def __iter__(self):
        for f in self._walk():
            yield f

    def save(self, obj):
        self._write(obj)

    def get(self, key):
        return self._load(key)
