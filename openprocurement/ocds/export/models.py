import jsonpatch
import itertools
from datetime import datetime
from couchdb import Database
from uuid import uuid4
from urllib import quote
from urlparse import urlparse, urlunparse
from itertools import chain
from openprocurement.ocds.export.helpers import (
    tender_converter,
    unique_tenderers,
    unique_documents,
    patch_converter,
    now,
    generate_uri,
    get_ocid
)
from openprocurement.ocds.export.convert import Converter
from couchdb.design import ViewDefinition
from couchdb_schematics.document import SchematicsDocument


invalidsymbols = ["`","~","!", "@","#","$", '"']

callbacks = {
    'minimalStep': ('minValue', lambda raw_data: raw_data.get('minimalStep')),
    'status': ('status', lambda raw_data: raw_data.get('status').split('.')[0]),
    'bids': ('tenderers', lambda raw_data: list(chain.from_iterable([b.get('tenderers') for b in raw_data.get('bids')]))),
    '_id': ('id', lambda raw_data: raw_data.get('_id')),
    'awards': ('awards', lambda raw_data: raw_data.get('awards')),
    'contracts': ('contracts', lambda raw_data: raw_data.get('contracts')),
    'dateModified': ('date', lambda raw_data: raw_data.get('dateModified')),
}


class Model(object):

    __slots__ = ()

    def __init__(self, raw_data):
        if isinstance(raw_data, dict):
            for key in raw_data:
                if key in callbacks:
                    self_key, func = callbacks[key]
                    data = func(raw_data)
                else:
                    self_key = key
                    data = raw_data.get(key)
                if data:
                    if self_key in self.__slots__ and self_key in modelsMap:
                        klass, _type = modelsMap.get(self_key)
                        if isinstance(_type, list):
                            setattr(self, self_key, [klass(x) for x
                                                     in data])
                        else:
                            setattr(self, self_key, klass(data))
                    elif self_key in self.__slots__:
                        setattr(self, self_key, data)

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
    initiationType = 'tender'
    language = 'uk'

    def __init__(self, raw_data, ocid='ocds-xxxx-'):
        data = {}
        data['tender'] = raw_data
        data['awards'] = raw_data.get('awards')
        data['contracts'] = raw_data.get('contracts')
        data['buyer'] = raw_data.get('procuringEntity')
        data.update(dict(ocid=ocid + raw_data.get('tenderID'),
                             id=uuid4().hex))
        super(Release, self).__init__(data)


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
    package = {}
    package['releases'] = [Release(r).__export__() for r in tenders]
    package['publishedDate'] = datetime.now().isoformat()
    package['publisher'] = config.get('publisher')
    package['license'] = 'https://creativecommons.org/publicdomain/zero/1.0/'
    return package
