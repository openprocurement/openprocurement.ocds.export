from utils import get_test_data
from ocds.export.helpers import get_field


def test_get_field():
    tender = get_test_data()
    assert tender['tenderID'] == get_field(tender, "tenderID")
    assert tender['procuringEntity'] == get_field(tender, "buyer")
