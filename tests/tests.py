import os.path
import json
from copy import deepcopy
from schematics.types import StringType
from ocds.export.helpers import (
    patch_converter,
    tender_converter,
    award_converter,
    unique_tenderers,
    unique_documents,
    get_ocid
)
from ocds.export.schema import (
    BaseModel,
    Status,
    Award,
    Contract,
    Tender
)

from ocds.export.models import (
    Release,
    ReleasePackage,
    Record,
    RecordPackage,
)
from ocds.export import release_tender

TEST_PERIOD = { "startDate": "2016-08-18T14:19:24.770873+03:00", "endDate": "2016-08-18T14:32:59.793234+03:00"}
TEST_ORGANIZATION = { "name": "test_name", "rogue_field": "rogue_field", "address": { "postalCode": "02221", "countryName": "TESK", "streetAddress": "STREET", "region": "Londod", "locality": "LONDON" }, "contactPoint": { "telephone": "11111111", "faxNumber": "", "name": "John Doe", "email": "john.doe@mail.net" }, "identifier": { "scheme": "UA-EDR", "legalName_en": "FOP-5", "id": "9009900990", "legalName": "legal name" }}
TEST_DOC = { "description": "description", "format": "application/pdf", "rogue_field": "rogue_field", "url": "https://tenders.org/test_id/documents/test_id?download=test_id", "title": "doc.pdf", "documentOf": "tender", "datePublished": "2016-08-18T12:52:26.909474+03:00", "dateModified": "2016-08-18T12:52:26.909497+03:00", "id": "test_id" }
TEST_AWARD = { "status": "active", "documents": [deepcopy(TEST_DOC) for _ in xrange(3)], "complaintPeriod": { "startDate": "2016-08-18T14:29:35.784443+03:00", "endDate": "2016-08-18T14:37:59.792947+03:00" }, "suppliers": [deepcopy(TEST_ORGANIZATION)], "eligible": True, "bid_id": "240ccf78ecb94b0e9cb13b0e45e8abf2", "value": { "currency": "UAH", "amount": 111, "valueAddedTaxIncluded": True }, "qualified": True, "date": "2016-08-18T14:32:59.805768+03:00", "id": "fb355c03f7eb481dbcbe0060e3deaff3" }
TEST_CONTRACT = {"status": "active", "documents": [deepcopy(TEST_DOC) for _ in xrange(3)], "items": [{"description": "item-titile", "classification": { "scheme": "CPV", "description": "TEST_CONTRACT", "id": "22100000-1" }, "additionalClassifications": [ { "scheme": "DKPP", "id": "52.21.21", "description": "description" } ], "deliveryLocation": { "latitude": "", "longitude": "" }, "deliveryAddress": { "countryName": "test_conuntry", "postalCode": "11111", "streetAddress": "STREET", "region": "LONDON", "locality": "LONDON" }, "deliveryDate": { "endDate": "2016-08-31T00:00:00+03:00" }, "id": "718c539c751f48b6bd5b7cb5bfca65d3", "unit": { "code": "E54", "name": "name" }, "quantity": 1 }], "suppliers": [deepcopy(TEST_ORGANIZATION)], "contractNumber": "2423/22-1", "period": deepcopy(TEST_PERIOD), "value": { "currency": "UAH", "amount": 111, "valueAddedTaxIncluded": False }, "dateSigned": "2016-08-19T09:58:00+03:00", "date": "2016-08-19T09:58:47.187060+03:00", "awardID": "fb355c03f7eb481dbcbe0060e3deaff3", "id": "ad6263fbb56443ba908ea4f45fbed465", "contractID": "UA-2016-08-18-000186-1"}
TEST_TENDER = {"procurementMethod": "open", "numberOfBids": 3, "awardPeriod": deepcopy(TEST_PERIOD), "complaintPeriod": deepcopy(TEST_PERIOD), "auctionUrl": "https://auction-sandbox.openprocurement.org/tenders/3bfaccf5a42d4cc8b601e940e149af8b", "enquiryPeriod": deepcopy(TEST_PERIOD), "submissionMethod": "electronicAuction", "procuringEntity": deepcopy(TEST_ORGANIZATION), "owner": "test-tender.com.ua", "id": "3bfaccf5a42d4cc8b601e940e149af8b", "description": "OPEN-TENDER", "documents": [deepcopy(TEST_DOC) for _ in xrange(3)], "title": "OPEN-TENDER", "tenderID": "UA-2016-08-18-000186", "procurementMethodDetails": "quick, accelerator=2880", "dateModified": "2016-08-19T09:58:47.187060+03:00", "status": "temp", "tenderPeriod": deepcopy(TEST_PERIOD), "contracts": [deepcopy(TEST_CONTRACT) for _ in xrange(3)], "auctionPeriod": deepcopy(TEST_PERIOD), "procurementMethodType": "aboveThresholdUA", "awards": [deepcopy(TEST_AWARD) for _ in xrange(3)], "date": "2016-08-19T09:58:47.187060+03:00", "submissionMethodDetails": "quick", "items": [ { "description": "NAME", "classification": { "scheme": "CPV", "description": "NAME", "id": "22100000-1" }, "additionalClassifications": [ { "scheme": "sdfs", "id": "52.21.21", "description": "SKDJSK" } ], "deliveryLocation": { "latitude": "", "longitude": "" }, "deliveryAddress": { "countryName": "UKRAINE", "postalCode": "11111", "streetAddress": "LONDON", "region": "LONDON", "locality": "LONDON" }, "deliveryDate": { "endDate": "2016-08-31T00:00:00+03:00" }, "id": "718c539c751f48b6bd5b7cb5bfca65d3", "unit": { "code": "E54", "name": "test" }, "quantity": 1 } ], "bids": [ { "status": "active", "selfEligible": True, "value": { "currency": "UAH", "amount": 111, "valueAddedTaxIncluded": False }, "selfQualified": True, "tenderers": [deepcopy(TEST_ORGANIZATION)], "date": "2016-08-18T12:56:02.385607+03:00", "id": "8fc3313a4896483b87d2f4f8df22a7d4", "participationUrl": "https://auction-sandbox.openprocurement.org/tenders/3bfaccf5a42d4cc8b601e940e149af8b/login?bidder_id=8fc3313a4896483b87d2f4f8df22a7d4&hash=f57217716180524ef737b399a2a0b59ff050c568" }, ], "value": { "currency": "UAH", "amount": 5000, "valueAddedTaxIncluded": False }, "minimalStep": { "currency": "UAH", "amount": 300, "valueAddedTaxIncluded": False }, "awardCriteria": "lowestCost"}


class TestHelpers(object):

    def test_parse_tender(self):
        tender = tender_converter(TEST_TENDER)
        assert 'bids' not in tender
        assert 'numberOfBids' not in tender
        assert 'minimalStep' not in tender

        assert 'tenderers' in tender
        assert 'minValue' in tender

    def test_parse_award(self):
        parsed_tender = award_converter(deepcopy(TEST_TENDER))
        assert TEST_TENDER != parsed_tender
        assert 'awards' in parsed_tender
        for award in parsed_tender['awards']:
            assert 'items' in award

    def test_parse_patch(self):
        patch = [
            { "op": "replace", "path": "/baz", "value": "boo" },
        ]
        amendment = patch_converter(patch)[0]
        assert amendment['property'] == '/baz'
        assert amendment['former_value'] == 'boo'

    def test_unique_tenderers(self):
        tenderers = unique_tenderers([TEST_ORGANIZATION, TEST_ORGANIZATION])
        assert len(tenderers) == 1
        assert tenderers[0] == TEST_ORGANIZATION
        new_organization = deepcopy(TEST_ORGANIZATION)
        new_organization['identifier']['id'] = '11111112222'
        new_organization['name'] = 'new name'
        assert new_organization['identifier']['id'] != TEST_ORGANIZATION['identifier']['id']

        tenderers = unique_tenderers([deepcopy(TEST_ORGANIZATION), new_organization])
        assert len(tenderers) == 2
        if tenderers[0]['name'] == 'new name':
            assert tenderers[0] == new_organization
            assert tenderers[1] == TEST_ORGANIZATION 
        else:
            assert tenderers[1] == new_organization
            assert tenderers[0] == TEST_ORGANIZATION 

    def test_unique_documents_id(self):
        doc1 = deepcopy(TEST_DOC)
        doc2 = deepcopy(TEST_DOC)
        docs = unique_documents([doc1, doc2])
        assert doc1['id'] == 'test_id-0'
        assert doc2['id'] == 'test_id-1'

    def test_get_ocid(self):
        assert get_ocid('a', 'b') == 'a-b'


class TestSchema(object):

    def test_base_model(self):

        class M(BaseModel):
            a = StringType()

        test_data = {'a': 'aa', 'b': 'bb'}
        inst = M(test_data)
        assert hasattr(inst, 'a')
        assert inst.a == 'aa'
        assert not hasattr(inst, 'b')

    def test_status_type(self):

        st = Status()
        assert 'active' == st.to_native('active')
        assert 'active' == st.to_native('active.test')
        assert 'complete' == st.to_native('complete')

    def test_award_model(self):
        award = Award(TEST_AWARD)
        assert not hasattr(award, 'bid_id')
        assert not hasattr(award.documents[0], 'rogue_field')
        doc_ids = set([d.id for d in award.documents])
        assert len(doc_ids) == 3

    def test_contract_model(self):
        contract = Contract(TEST_CONTRACT)
        assert not hasattr(contract, 'contractNumber')
        assert not hasattr(contract.documents[0], 'rogue_field')
        doc_ids = set([d.id for d in contract.documents])
        assert len(doc_ids) == 3


    def test_tender_model(self):
        tender = Tender(TEST_TENDER)
        assert not hasattr(tender, 'owner')
        assert not hasattr(tender, 'bids')
        assert hasattr(tender, 'tenderers')
        assert tender.numberOfTenderers == 1
        tender1 = deepcopy(TEST_TENDER)
        tender2 = deepcopy(TEST_TENDER)
        tender2['tenderPeriod']['startDate'] = 'new_date'

        tender = Tender.with_diff(tender1, tender2)

        assert tender.tenderPeriod.startDate == 'new_date'
        assert tender.amendment.date == tender2['dateModified']
        assert tender.amendment.changes[0].property == '/tenderPeriod/startDate'
        assert tender.amendment.changes[0].former_value == TEST_PERIOD['startDate'] 


class TestModels(object):

    def test_release(self):
        tender = deepcopy(TEST_TENDER)
        release = Release(tender)
        assert release.tag == ['tender', 'award', 'contract']
        assert release.buyer['name'] == TEST_TENDER['procuringEntity']['name']
        assert hasattr(release, 'tender') and getattr(release, 'tender')
        assert hasattr(release, 'awards') and getattr(release, 'awards')
        assert hasattr(release, 'contracts') and getattr(release, 'contracts')
        assert release.initiationType == 'tender'

        tender = deepcopy(TEST_TENDER)
        del tender['awards']
        release = Release(tender)
        assert hasattr(release, 'awards') and not getattr(release, 'awards')

    def test_release_package(self):
        releases = [Release(TEST_TENDER) for _ in xrange(3)]
        package = ReleasePackage(dict(releases=releases))
        assert len(package.releases) == 3

    def test_record(self):
        pass

    def test_release_tender(self):
        release = release_tender(TEST_TENDER, 'test')
        assert release.date ==  TEST_TENDER['dateModified']
        assert isinstance(release, Release)
        assert release.ocid == "test-UA-2016-08-18-000186"

    def test_release_tenders(self):
        pass
