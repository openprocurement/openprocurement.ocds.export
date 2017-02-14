import jsonpatch
import itertools
from datetime import datetime
from uuid import uuid4
from itertools import chain
from openprocurement.ocds.export.helpers import (
    unique_tenderers,
    unique_documents,
    award_converter,
    now,
    get_ocid,
    build_package
)


callbacks = {
    'minValue': lambda raw_data: raw_data.get('minimalStep'),
    'status': lambda raw_data: raw_data.get('status').split('.')[0],
    'documents': lambda raw_data: unique_documents(raw_data.get('documents')),
    'tenderers': lambda raw_data: unique_tenderers(list(chain.from_iterable([b.get('tenderers') for b in raw_data.get('bids', [])]))),
    'id': lambda raw_data: raw_data.get('_id') if '_id' in raw_data else raw_data.get('id'),
    'awards': lambda raw_data: award_converter(raw_data),
    'contracts': lambda raw_data: raw_data.get('contracts'),
    'date': lambda raw_data: raw_data.get('dateModified'),
    'tender': lambda raw_data: raw_data,
    'buyer': lambda raw_data: raw_data.get('procuringEntity')
}


class Model(object):

    __slots__ = ()

    def __init__(self, raw_data):
        for key in self.__slots__:
            data = None
            if key in callbacks:
                data = callbacks[key](raw_data)
            elif key in raw_data:
                data = raw_data.get(key)
            if data:
                if key in modelsMap:
                    klass, _type = modelsMap.get(key)
                    if isinstance(_type, list):
                        setattr(self, key, [klass(x) for x in data])
                    else:
                        setattr(self, key, klass(data))
                else:
                    setattr(self, key, data)

    def __export__(self):
        data = {}
        for k in [f for f in dir(self) if not f.startswith('__')]:
            attr = hasattr(self, k) and getattr(self, k)
            if attr:
                if isinstance(attr, Model):
                    data[k] = attr.__export__()
                elif isinstance(attr, (tuple, list)):
                    data[k] = [x.__export__() for x in attr]
                else:
                    data[k] = attr
        return data


class Document(Model):

    __slots__ = (
        'id',
        'documentType',
        'title',
        'description',
        'url',
        'datePublised',
        'dateModified',
        'format',
        'language'
    )


class Classification(Model):

    __slots__ = (
        'scheme',
        'id',
        'description',
        'uri'
    )


class Contact(Model):

    __slots__ = (
        'name',
        'email',
        'telephone',
        'faxNumber',
        'url'
    )


class Unit(Model):

    __slots__ = (
        'name',
        'value'
    )


class Period(Model):

    __slots__ = (
        'startDate',
        'endDate'
    )


class Identifier(Model):

    __slots__ = (
        'scheme',
        'id',
        'legalName',
        'uri'
    )


class Value(Model):

    __slots__ = (
        'amount',
        'currency'
    )


class Address(Model):

    __slots__ = (
        'streetAddress',
        'locality',
        'postalCode',
        'countryName',
    )


class Item(Model):

    __slots__ = (
        'id',
        'description',
        'classification',
        'additionalClassifications',
        'quantity',
        'unit'
    )


class Organization(Model):

    __slots__ = (
        'identifier',
        'additionalIdentifiers',
        'name',
        'address',
        'contactPoint'
    )


class Award(Model):

    __slots__ = (
        'id',
        'title',
        'description',
        'status',
        'date',
        'value',
        'suppliers',
        'items',
        'contractPeriod',
        'documents',
    )

class Contract(Model):

    __slots__ = (
        'id',
        'awardID',
        'title',
        'description',
        'status',
        'period',
        'value',
        'items',
        'dateSigned',
        'documents',

    )


class Tender(Model):

    __slots__ = (
        'id',
        'title',
        'description',
        'status',
        'items',
        'minValue',
        'value',
        'procurementMethod',
        'procurementMethodRationale',
        'awardCriteria',
        'awardCriteriaDetails',
        'submissionMethod',
        'submissionMethodDetails',
        'tenderPeriod',
        'enquiryPeriod',
        'hasEnquiries',
        'eligibilityCriteria',
        'awardPeriod',
        'tenderers',
        'procuringEntity',
        'documents',
    )

    @property
    def numberOfTenderers(self):
        return len(self.tenderers)


class Release(Model):

    __slots__ = (
        'id',
        'date',
        'ocid',
        'language',
        'initiationType',
        'tender',
        'awards',
        'contracts',
        'buyer',
        'tag'
    )
    
    def __init__(self, raw_data, ocid='ocds-xxxx-'):
        self.initiationType = 'tender'
        self.language = 'uk'
        super(Release, self).__init__(raw_data)
        self.ocid = get_ocid(ocid, raw_data.get('tenderID'))
        self.id = uuid4().hex


modelsMap = {
    'documents': (Document, []),
    'tender': (Tender, {}),
    'tenderPeriod': (Period, {}),
    'enquiryPeriod': (Period, {}),
    'contractPeriod': (Period, {}),
    'period': (Period, {}),
    'awardPeriod': (Period, {}),
    'tenderers': (Organization, []),
    'suppliers': (Organization, []),
    'procuringEntity': (Organization, {}),
    'buyer': (Organization, {}),
    'address': (Address, {}),
    'value': (Value, {}),
    'minValue': (Value, {}),
    'items': (Item, []),
    'identifier': (Identifier, {}),
    'classification': (Classification, {}),
    'unit': (Unit, {}),
    'contactPoint': (Contact, {}),
    'additionalIdentifiers': (Identifier, []),
    'additionalClassifications': (Classification, []),
    'awards': (Award, []),
    'contracts': (Contract, [])
}


def release_tender(tender, prefix):
    release = Release(tender, prefix)
    return release.__export__()


def package_tenders(tenders, config):
    package = build_package(config)
    package['releases'] = [release_tender(t, config.get('prefix')) for t in tenders]
    return package
