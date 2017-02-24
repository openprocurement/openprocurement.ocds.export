import pytest
import couchdb
from openprocurement.ocds.export.storage import (
    TendersStorage,
)


coudb_url = 'http://admin:admin@127.0.0.1:5984'
db_name  = 'test'
SERVER = couchdb.Server(coudb_url)

test_tender = {
    "date": "2016-09-28t14:57:14.846483+03:00",
    "id": "0009417e6dd1413585426be68bf6a4dd",
    "test": "test",
    "dateModified": "2016-09-28t14:57:14.846483+03:00",
    "tenderID": "test"
}

test_release = {
   "_id": "kjndsafjnaioej1029i31029i21",
   "date": "2016-12-22T00:01:21.412411+00:00",
   "ocid": "ocds-xxxxxx-UA-2016-12-21-000333-a",
   "language": "uk",
   "initiationType": "tender",
   "buyer": {
       "identifier": {
           "scheme": "UA-EDR",
           "id": "01208375",
           "legalName": "test"
       },
       "name": "test",
       "address": {
           "streetAddress": "test",
           "locality": "test",
           "postalCode": "test",
           "countryName": "test"
       },
       "contactPoint": {
           "name": "sdjfkfdsflk ",
           "email": "skdnfdslf n",
           "telephone": "",
           "faxNumber": ""
       }
   },
   "tender": {
       "title": "sdnfsdjdk nsldjn",
       "description": "skdjnf dsnf",
       "status": "complete",
       "items": [
           {
               "id": "fac6e50704d97448eddc563c5d7ac5d2",
               "description": "skdj nfdsln",
               "classification": {
                   "scheme": "CPV",
                   "id": "45223810-7",
                   "description": "skdjfnsd jn"
               },
               "additionalClassifications": [
                   {
                       "scheme": "sld jfd",
                       "id": "1261.9",
                       "description": "kjds nflj "
                   }
               ],
               "quantity": 1,
               "unit": {
                   "name": "i"
               }
           }
       ],
       "value": {
           "amount": 1243242,
           "currency": "UAH"
       },
       "procurementMethod": "limited",
       "procuringEntity": {
           "identifier": {
               "scheme": "UA-EDR",
               "id": "01208375",
               "legalName": "sdkjf ns"
           },
           "name": "isdf kjnsj",
           "address": {
               "streetAddress": "dskj nf",
               "locality": "skdjf nslkjn",
               "postalCode": "30421",
               "countryName": "sd nfkjnds kn"
           },
           "contactPoint": {
               "name": "sdkjf nkdsj nfjdsk ",
               "email": "ksjnfdskjnf@ukr.net",
               "telephone": "skd jfds kj",
               "faxNumber": "sdkj nfkjds nkjd s"
           }
       },
       "id": "ccff2b43sdf2o223je30932e2",
       "numberOfTenderers": 0
   },
   "tag": [
       "tender",
   ]
}


@pytest.fixture(scope='function')
def db(request):
    def delete():
        del SERVER[db_name]

    if db_name in SERVER:
        delete() 
    SERVER.create(db_name)
    request.addfinalizer(delete)

@pytest.fixture(scope='function')
def storage(request):
    storage = TendersStorage(coudb_url, db_name)
    storage.save(test_tender)
    return storage



class TestStorage(object):
    
    @pytest.mark.parametrize('storage', [TendersStorage])
    def test_create(self, storage):
        if db_name in SERVER:
            del SERVER[db_name]
        storage = storage(coudb_url, db_name)
        assert db_name in SERVER
    
    def test_tender_iter(self, db, storage):
        for item in storage:
            assert item == test_tender

    def test_tender_date_modified(self, db, storage):
        for resp in storage.view('tenders/by_dateModified'):
            assert resp['value'] == test_tender['dateModified']
    
    def test_release_iter(self, db, storage):
        for item in storage:
            assert item == test_release
