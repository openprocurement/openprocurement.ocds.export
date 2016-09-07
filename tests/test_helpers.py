from ocds.export.helpers import (
    parse_tender,
    parse_award
)
from utils import get_test_data
from copy import deepcopy


def test_parse_tender():
    tender = parse_tender(get_test_data())
    assert 'bids' not in tender
    assert 'numberOfBids' not in tender
    assert 'minimalStep' not in tender

    assert 'tenderers' in tender
    assert 'numberOfTenderers' in tender
    assert 'minValue' in tender


def test_parse_award():
    orig_tender = get_test_data()
    parsed_tender = parse_award(deepcopy(orig_tender))
    assert orig_tender != parsed_tender
    assert 'awards' in parsed_tender
    for award in parsed_tender['awards']:
        assert 'items' in award


def test_get_field():
    pass


def test_get_tags():
    pass
