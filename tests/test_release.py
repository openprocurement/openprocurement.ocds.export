from utils import get_test_data
from ocds.export.release import get_release_from_tender


def test_tender_release():
    tender = ((get_test_data()))
    release = get_release_from_tender(tender, 'sd')
    if tender['status'] not in ['complete', 'unsuccessful', 'cancelled']:
        assert release['tender']['status'] == 'active'
    assert (release['tender']['numberOfTenderers']) == len(release['tender']['tenderers'])
    _ids = [i['identifier']['id'] for i in release['tender']['tenderers']]
    assert len(set(_ids)) == len(_ids)
