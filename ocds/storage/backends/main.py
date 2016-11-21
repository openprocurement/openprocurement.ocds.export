from ..backends.couch import TendersStorage, ReleasesStorage
from ocds.storage.backends.fs import FSStorage
import os
from ocds.export.release import do_releases
from ocds.storage.models import ReleaseDoc


class MainStorage(object):

    def __init__(self, config, basepath):
        self.rel_storage = ReleasesStorage(config.get("releases_db"))
        self.ten_storage = TendersStorage(config.get("tenders_db"))
        self.fs_storage = FSStorage(basepath)
        self.info = config.get('release')
        self.basepath = basepath

    def __contains__(self, key):
        for res in self.rel_storage.get_ocid(key):
            if res:
                return True
            else:
                return False

    def get_rel_for_record(self):
        for releases in self.rel_storage.get_finished_ocids():
            rels = []
            for release in releases:
                rels.append(self.fs_storage.read_by_full_path(release))
            yield rels

    def is_finished(self, status):
        if status in ['complete', 'unsuccesful', 'cancelled']:
            return True
        else:
            return False

    def form_doc(self, ocid, path, status, _id):
        return ReleaseDoc(_id=_id,
                          path=path,
                          ocid=ocid,
                          finished=self.is_finished(status)
                          ).__dict__['_data']

    def _write(self):
        for tenders in self.ten_storage:
            for release in do_releases(tenders, self.info['prefix']):
                _id = release['id']
                self.fs_storage.save(release)
                path = os.path.join(
                    self.basepath, self.fs_storage._path_from_date(release['date']))
                self.rel_storage.save(self.form_doc(release['ocid'],
                                                    path,
                                                    release['tender']['status'],
                                                    _id)
                                      )

    def save(self):
        self._write()
