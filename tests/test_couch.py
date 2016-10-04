import unittest
from ocds.storage.backends.couchdbst import CouchStorage
from ocds.storage.helpers import get_config_from_file, get_release_from_file


class TestCouchStorage(unittest.TestCase):

    def test_init(self):
        config = get_config_from_file('config.yaml')
        self.assertIsInstance(config, dict)
        couchst = CouchStorage(config)

    def test_post(self):
        config = get_config_from_file('config.yaml')
        couchst = CouchStorage(config)
        doc = get_release_from_file('release1.json')
        ocids = couchst.get_releases_ocids()
        if not (couchst.post(doc, ocids)):
            doc1 = couchst.get_by_ocid_and_max_date(doc['ocid'])
            doc['tag'] = couchst.get_diff_and_tag(doc, doc1)
            couchst.post(doc, ocids, True)

if __name__ == '__main__':
    unittest.main()
