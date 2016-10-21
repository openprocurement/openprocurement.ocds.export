from ocds.export.helpers import check_releases
import os
from ocds.export.record import Record


basepath = os.path.dirname(__file__)


def test_record():
    test_release1 = {
        "ocid": "test",
        "date": "qwe",
        "tender": {
            "status": "active"
        }
    }
    test_release2 = {
        "ocid": "test",
        "date": "qwe",
        "tender": {
            "status": "cancelled"
        }
    }
    releases = [test_release1, test_release2]
    assert check_releases(releases)
    record = Record(releases, releases[0]['ocid'])
    assert record
    assert record['releases']
    assert record['compiledRelease']['tag'][0] == "compiled"
