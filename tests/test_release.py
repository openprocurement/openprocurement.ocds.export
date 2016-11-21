from utils import get_test_data
from ocds.export.release import get_release_from_tender


def test_tender_release():
    tender = get_test_data()
    assert tender['bids']
    assert tender['submissionMethod']
    assert tender['minimalStep']
    release = get_release_from_tender(tender, 'test')
    if tender['status'] not in ['complete', 'unsuccessful', 'cancelled']:
        assert release['tender']['status'] == 'active'
    assert (release['tender']['numberOfBids']) == len(release['tender']['bids'])
    tenderers_ids = [k['identifier']['id'] for i in release['tender']['bids'] for k in i['tenderers']]
    assert len(set(tenderers_ids)) == len(tenderers_ids)
    tender_doc_ids = [i['id'] for i in release['tender']['documents']]
    assert len(set(tender_doc_ids)) == len(tender_doc_ids)
    award_doc_ids = [k['id'] for i in release['awards'] for k in i['documents']]
    contract_doc_ids = [k['id'] for i in release['contracts'] for k in i['documents']]
    assert len(set(award_doc_ids)) == len(award_doc_ids)
    assert len(set(contract_doc_ids)) == len(contract_doc_ids)
