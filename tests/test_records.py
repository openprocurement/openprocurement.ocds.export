from ocds.export.helpers import get_same_ocid_releases, get_ocids, generate_uri
import os
from utils import get_releases
from ocds.export.record import Record
basepath = os.path.dirname(__file__)


def test_record():
    releases = get_releases(os.path.join(basepath, 'releases'))
    ocids = set(get_ocids(releases))
    publisher = {
        "name": "\u0414\u041f \"\u041f\u0440\u043e\u0437\u043e\u0440\u0440\u043e\""
    }
    for ocid in ocids:
        if get_same_ocid_releases(releases, ocid):
            assert Record(ocid, get_same_ocid_releases(releases, ocid), publisher, generate_uri())