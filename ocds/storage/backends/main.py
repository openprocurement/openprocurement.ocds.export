from ..backends.couch import TendersStorage, ReleasesStorage
from ocds.storage.backends.fs import FSStorage
import os
from ocds.export.release import get_release_from_tender
from ocds.storage.models import ReleaseDoc


class MainStorage(object):

    def __init__(self, config, basepath):
        self.rel_storage = ReleasesStorage(config.get("releases_db"))
        self.ten_storage = TendersStorage(config.get("tenders_db"))
        self.fs_storage = FSStorage(basepath)
        self.info = config.get('release')
        self.basepath = basepath

    def _find(self, ocid):
        if self.rel_storage.get_ocid(ocid):
            return True
        else:
            return False

    def __contains__(self, key):
        self._find(key)

    def is_finished(self, status):
        if status in ['complete', 'unsuccesful', 'cancelled']:
            return True
        else:
            return False

    def form_doc(self, ocid, path, status):
        return ReleaseDoc(path=path,
                          ocid=ocid,
                          finished=self.is_finished(status),
                          same_ocids=self._find(ocid)
                          ).__dict__['_data']

    def _write(self):
        for tender in self.ten_storage:
            release = get_release_from_tender(tender, self.info.get('prefix'))
            self.fs_storage.save(release)
            path = os.path.join(
                self.basepath, self.fs_storage._path_from_date(tender['date']))
            self.rel_storage.save(self.form_doc(release['ocid'],
                                                path,
                                                tender['status'])
                                  )

    def save(self):
        self._write()
