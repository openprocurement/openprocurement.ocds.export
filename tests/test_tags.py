import pytest
from utils import get_test_data, test_schema
from ocds.export.tag import (
    Mapping,
    Tender,
    Award,
    Contract,
    Buyer,
    Tag
)
from ocds.export.helpers import (
    parse_tender
)


def test_tender():
    assert Tender.__tag__ == 'tender'
    tender = Tender(parse_tender(get_test_data()))


def test_buyer():
    assert Buyer.__tag__ == 'buyer'


def test_contract():
    assert Contract.__tag__ == 'contracts'


def test_award():
    assert Award.__tag__ == 'awards'


def test_tag():
    tag = Tag('awards', get_test_data())
    assert isinstance(tag, Award)

    tag = Tag('contracts', get_test_data())
    assert isinstance(tag, Contract)

    tag = Tag('tender', parse_tender(get_test_data()))
    assert isinstance(tag, Tender)

    tag = Tag('buyer', get_test_data())
    assert isinstance(tag, Buyer)
