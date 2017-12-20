import jsonpatch
import logging
from uuid import uuid4
from openprocurement.ocds.export.helpers import (
    unique_tenderers,
    unique_documents,
    award_converter,
    get_ocid,
    build_package,
    compile_releases,
    convert_status
)

logger = logging.getLogger(__name__)


callbacks = {
    'status': lambda raw_data: convert_status(raw_data),
    'documents': lambda raw_data: unique_documents(raw_data.get('documents')),
    'tenderers': lambda raw_data: unique_tenderers(raw_data),
    'id': lambda raw_data: raw_data.get('_id') if '_id' in raw_data else raw_data.get('id'),
    'awards': lambda raw_data: award_converter(raw_data),
    'contracts': lambda raw_data: raw_data.get('contracts'),
    'date': lambda raw_data: raw_data.get('dateModified', raw_data.get('date', '')),
    'tender': lambda raw_data: raw_data,
    'buyer': lambda raw_data: raw_data.get('procuringEntity'),
    'submissionMethod': lambda raw_data: [raw_data.get('submissionMethod', '')],
}


class Model(object):

    __slots__ = ()

    def __init__(self, raw_data, modelsMap, callbacks):
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
                        setattr(self, key, [klass(x, modelsMap, callbacks) for x in data])
                    else:
                        setattr(self, key, klass(data, modelsMap, callbacks))
                else:
                    setattr(self, key, data)

    def __export__(self):
        data = {}
        for k in [f for f in dir(self) if not f.startswith('__')]:
            attr = hasattr(self, k) and getattr(self, k)
            if attr:
                exported = {}
                if isinstance(attr, Model):
                    exported = attr.__export__()
                elif isinstance(attr, (tuple, list)):
                    exported = [
                        x.__export__()
                        if hasattr(x, '__export__')
                        else x for x in attr
                        if x
                    ]
                else:
                    exported = attr
                if exported:
                    data[k] = exported
        return data


class Document(Model):

    __slots__ = (
        'id',
        'documentType',
        'title',
        'description',
        'url',
        'datePublished',
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

    def __init__(self, raw_data, modelsMap, callbacks, ocid='ocds-xxxx-'):
        self.initiationType = 'tender'
        self.language = 'uk'
        super(Release, self).__init__(raw_data, modelsMap, callbacks)
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


def release_tender(tender, modelsMap, callbacks, prefix):
    release = Release(tender, modelsMap, callbacks, prefix).__export__()
    tag = ['tender']
    for op in ['awards', 'contracts']:
        if op in release:
            tag.append(op[:-1])
    release['tag'] = tag
    return release


def release_tenders(tender, modelsMap, callbacks, prefix):

    def prepare_first_tags(release):
        tag = ['tender']
        for f in ['awards', 'contracts']:
            if f in release:
                tag.append(f[:-1])
        return list(set(tag))

    assert 'patches' in tender
    patches = tender.pop('patches')

    first_release = Release(tender, modelsMap, callbacks).__export__()
    first_release['tag'] = prepare_first_tags(first_release)
    releases = [first_release]
    for patch in patches:
        tender = jsonpatch.apply_patch(tender, patch)
        next_release = Release(tender, modelsMap, callbacks).__export__()
        if first_release != next_release:
            diff = jsonpatch.make_patch(first_release, next_release).patch
            tag = []
            for op in diff:
                if op['path'] in ['/tag', '/id']:
                    continue
                if op['op'] != 'add':
                    if not any(p in op['path'] for p in ['awards', 'contracts']):
                        tag.append('tenderUpdate')
                    else:
                        for p in ['awards', 'contracts']:
                            if p in op['path']:
                                tag.append(p[:-1] + 'Update')
                else:
                    for p in ['awards', 'contracts']:
                        if p in op['path']:
                            tag.append(p[:-1])
            next_release['tag'] = list(set(tag))
            releases.append(next_release)
        first_release = next_release
    return releases


def record_tenders(tender, modelsMap, callbacks, prefix):
    record = {}
    record['releases'] = release_tenders(tender, modelsMap, callbacks, prefix)
    record['compiledRelease'] = compile_releases(record['releases'])
    record['ocid'] = record['releases'][0]['ocid']
    return record


def package_tenders(tenders, modelsMap, callbacks, config):
    package = build_package(config)
    releases = []
    for tender in tenders:
        if not tender:
            continue
        if 'patches' in tender:
            releases.extend(release_tenders(tender, config.get('prefix')))
        else:
            releases.append(release_tender(tender, modelsMap, callbacks, config.get('prefix')))
    package['releases'] = releases
    return package


def package_records(tenders, modelsMap, callbacks, config):
    package = build_package(config)
    records = []
    for tender in tenders:
        if not tender:
            continue
        records.append(record_tenders(tender, modelsMap, callbacks, config.get('prefix')))
    package['records'] = records
    return package


def compare_data(data, ocds_data):
    ext = {}
    for key in data:
        if key not in ocds_data:
            ext[key] = data[key]
        elif data[key] != ocds_data[key]:
            if isinstance(data[key], list):
                ext[key] = [compare_data(k, ocds_data[key][i]) for i, k in enumerate(data[key])]
            elif isinstance(data[key], dict):
                ext[key] = compare_data(data[key], ocds_data[key])
            else:
                ext[key] = data[key]
        if data.get('id'):
            ext['id'] = data['id']
    return ext


def get_extensions(tender):
    new_tender = {}
    data = {}
    ocds_data = release_tender(tender, modelsMap, callbacks, 'ocds-be6bcu')
    for field in ['awards', 'contracts']:
        if field in tender:
            new_tender[field] = tender.pop(field)
    new_tender['tender'] = tender
    new_tender['buyer'] = new_tender.get('tender').pop('procuringEntity')
    data['ocds'] = ocds_data
    data['extensions'] = compare_data(new_tender, ocds_data)
    return data
