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
    test_release_with_lot_value = {
        "ocid": "test",
        "date": "qwe",
        "tender": {
            "status": "cancelled",
            "bids": [
                {
                    "lotValues": [{"test": "test"}]
                }]
        }
    }
    releases = [test_release1, test_release2]
    record = Record(releases, releases[0]['ocid'])
    assert len(record['releases']) == 2
    assert record['compiledRelease']['tag'][0] == "compiled"
    record = Record([test_release_with_lot_value], releases[0]['ocid'])
    assert "id" not in record['compiledRelease']['tender']['bids'][0]['lotValues'][0].keys()
