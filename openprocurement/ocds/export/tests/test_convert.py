from openprocurement.ocds.export.helpers import (
    unique_tenderers,
    unique_documents,
    convert_cancellation,
    prepare_cancellation_documents,
    convert_questions,
    award_converter,
    convert_bids,
    convert_unit_and_location,
    create_auction,
)

from .utils import (
    tender,
    award,
    document,
    cancellation,
    question
)
from copy import deepcopy


class TestConvertHelpers(object):

    def test_unique_tenderers(self):
        bid = tender['bids'][0]
        tenderers = unique_tenderers([bid.copy(),
                                      bid.copy()])
        assert len(tenderers) == 1
        assert tenderers[0] == bid['tenderers'][0]
        new_bid = deepcopy(bid)
        new_bid['tenderers'][0]['identifier']['id'] = '11111112222'
        new_bid['tenderers'][0]['name'] = 'new name'

        tenderers = unique_tenderers([bid.copy(), new_bid])
        assert len(tenderers) == 2
        assert tenderers[1] == new_bid['tenderers'][0]
        assert tenderers[0] == bid['tenderers'][0]

    def test_unique_documents(self):
        _id = document['id']
        docs = unique_documents([deepcopy(document) for _ in range(2)])
        for i, doc in enumerate(docs):
            assert doc['id'] == _id + '-{}'.format(i)

    def test_convert_cancellation(self):
        ten = deepcopy(tender)
        lot_canc = cancellation.copy()
        lot_canc['relatedLot'] = '73039fc5ebf944b19d43a2122c4c3e8b'
        lot_canc['cancellationOf'] = 'lot'
        ten['cancellations'] = [cancellation.copy(), lot_canc]
        convert_cancellation(ten)
        assert 'pendingCancellation' in ten
        assert 'pendingCancellation' in ten['lots'][0]

    def test_prepare_cancellation_documents(self):
        docs = prepare_cancellation_documents(cancellation.copy())
        assert docs[0]['documentType'] == 'tenderCancellation'
        lot_canc = cancellation.copy()
        lot_canc['cancellationOf'] = 'lot'
        docs = prepare_cancellation_documents(lot_canc)
        assert docs[0]['documentType'] == 'lotCancellation'

    def test_convert_question(self):
        assert 'relatedItem' in question
        ten = deepcopy(tender)
        ten['questions'] = [question.copy()]
        new = convert_questions(ten)
        assert 'relatedItem' not in new[0]
        assert 'relatedLot' in new[0]

    def test_award_converter(self):
        ten = deepcopy(tender)
        ten['awards'] = [deepcopy(award)]
        aw = award_converter(ten)[0]
        assert 'items' in aw

    def test_convert_bids(self):
        bid = tender['bids']
        bids = convert_bids(bid)
        assert 'details' in bids
        assert len(bids['details']) == len(bid[0]['lotValues'])

    def test_convert_unit_and_location(self):
        items = tender['items']
        new = convert_unit_and_location(items)
        new_loc = new[0]['deliveryLocation']
        new_unit = new[0]['unit']
        assert 'geometry' in new_loc
        assert 'coordinates' in new_loc['geometry']
        assert isinstance(new_loc['geometry']['coordinates'], list)
        assert 'id' in new_unit

    def test_create_auction(self):
        data = deepcopy(tender)
        auction = create_auction(data)
        assert auction is not None
        for key in ['minimalStep', 'period', 'url']:
            assert key in auction[0]
            assert key in auction[1]
