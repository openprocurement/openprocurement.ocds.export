from openprocurement.ocds.export.models import (
    Award,
    Contract,
    Tender,
    release_tender,
    release_tenders,
    package_tenders,
    record_tenders,
    modelsMap,
    callbacks
)
from openprocurement.ocds.export.ext.models import (
    TenderExt,
    AwardExt,
    ContractExt,
    update_models_map,
    update_callbacks,
    release_tender_ext,
    release_tenders_ext,
    record_tenders_ext,
    package_tenders_ext
)
from .utils import (
    award,
    contract,
    tender,
    config
)


class TestModels(object):

    def test_award_model(self):
        new = Award(award).__export__()
        assert 'lotID' not in new
        assert 'bidID' not in new

    def test_contract_model(self):
        new = Contract(contract).__export__()
        assert 'suppliers' not in new
        assert 'contractID' not in new
        assert 'contractNumber' not in new

    def test_tender_model(self):
        new = Tender(tender).__export__()
        assert 'bids' not in new
        assert 'lots' not in new
        assert 'tenderID' not in new


class TestModelsExt(object):

    def test_award_model(self):
        new = AwardExt(award).__export__()
        assert 'lotID' in new

    def test_tender_model(self):

        new = TenderExt(tender).__export__()
        assert 'lots' in new
        assert 'tenderID' in new

    def test_contract_model(self):
        new = ContractExt(contract).__export__()
        assert 'contractNumber' in new
        assert 'contractID' in new


class TestExport(object):

    def test_release_tender(self):
        ten = tender.copy()
        ten['awards'] = [award.copy()]
        ten['contracts'] = [contract.copy()]
        release = release_tender(ten, 'test')
        assert 'ocid' in release
        assert release['ocid'] == 'test-{}'.format(ten['tenderID'])
        assert release['date'] == ten['dateModified']
        assert release['tag'] == ['tender', 'award', 'contract']
        assert 'bids' not in release
        assert 'bid' not in release['tag']

    def test_release_package(self):
        pack = package_tenders([tender for _ in xrange(3)], config)
        assert len(pack['releases']) == 3
        for field in ['license', 'publicationPolicy']:
            assert field in pack
            assert pack[field] == 'test'
        assert 'name' in pack['publisher']
        assert pack['publisher']['name'] == 'test'

    def test_release_tenders(self):
        patch1 = [
            {"op": "add",
             "path": "/test",
             "value": "test"}
        ]
        ten = tender.copy()
        ten['patches'] = [patch1]
        releases = release_tenders(ten, 'test')
        assert len(releases) == 2
        assert 'tenderUpdate' not in releases[1]
        patch2 = [
            {"op": "replace",
             "path": "/description",
             "value": "test"
             }
        ]
        ten['patches'] = [patch2]
        releases = release_tenders(ten, 'test')
        assert 'tenderUpdate' in releases[1]['tag']
        assert releases[0]['tender']['description'] != 'test'
        assert releases[1]['tender']['description'] == 'test'
        ten['awards'] = [award]
        patch3 = [
            {"op": "replace",
             "path": "/awards/0/status",
             "value": "test"
             }
        ]
        ten['patches'] = [patch3]
        releases = release_tenders(ten, 'test')
        assert 'awardUpdate' in releases[1]['tag']
        assert releases[0]['awards'][0]['status'] != 'test'
        assert releases[1]['awards'][0]['status'] == 'test'
        patch4 = [
            {"op": "replace",
             "path": "/contracts/0/status",
             "value": "test"
             }
        ]
        ten['contracts'] = [contract]
        ten['patches'] = [patch3, patch4]
        releases = release_tenders(ten, 'test')
        assert 'awardUpdate' in releases[1]['tag']
        assert 'contractUpdate' in releases[2]['tag']
        assert releases[1]['awards'][0]['status'] == 'test'
        assert releases[2]['contracts'][0]['status'] == 'test'
        patch5 = [{'op': 'add', 'path': '/contracts',
          'value': [{'status': 'test', 'description': 'Some test contract'
          }]}]
        ten = tender.copy()
        ten['patches'] = [patch5]
        releases = release_tenders(ten, 'test')

    def test_record(self):
        ten = tender.copy()
        patch = [
            {"op": "replace",
             "path": "/description",
             "value": "test"
             }
        ]
        ten['patches'] = [patch]
        record = record_tenders(ten, 'test')
        assert len(record['releases']) == 2
        assert record['ocid'] == record['releases'][0]['ocid']


class TestExportExt(object):

    def test_models_map_update(self):
        update_models_map()
        assert "bids" in modelsMap

    def test_callbacks_update(self):
        update_callbacks()
        assert 'bids' in callbacks

    def test_release_tender(self):
        release = release_tender_ext(tender, 'test')
        assert 'bid' in release['tag']

    def test_release_tenders(self):
        ten = tender.copy()
        patch = [
            {"op": "replace",
             "path": "/bids/0/status",
             "value": "test"
             }
        ]
        ten['patches'] = [patch]
        releases = release_tenders_ext(ten, 'test')
        assert len(releases) == 2
        assert 'bidUpdate' in releases[1]['tag']
        patch1 = [
            {"op": "replace",
             "path": "/description",
             "value": "test"
             }
        ]
        ten['patches'] = [patch1]
        releases = release_tenders_ext(ten, 'test')
        assert 'tenderUpdate' in releases[1]['tag']
        patch2 = [{'op': 'add', 'path': '/bids/1',
          'value': {'status': 'test', 'description': 'Some test bid',
          }}]
        ten = tender.copy()
        ten['patches'] = [patch2]
        releases = release_tenders_ext(ten, 'test')
        assert 'bid' in releases[1]['tag']

    def test_release_package(self):
        pack = package_tenders_ext([tender for _ in xrange(3)], config)
        assert len(pack['releases']) == 3
        for field in ['license', 'publicationPolicy']:
            assert field in pack
            assert pack[field] == 'test'
        assert 'name' in pack['publisher']
        assert pack['publisher']['name'] == 'test'

    def test_record(self):
        ten = tender.copy()
        patch = [
            {"op": "replace",
             "path": "/description",
             "value": "test"
             }
        ]
        ten['patches'] = [patch]
        record = record_tenders_ext(ten, 'test')
        assert len(record['releases']) == 2
        assert record['ocid'] == record['releases'][0]['ocid']
