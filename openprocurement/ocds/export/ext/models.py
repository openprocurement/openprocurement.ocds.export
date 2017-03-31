import jsonpatch
from openprocurement.ocds.export.models import (
    Award,
    Tender,
    Contract,
    Item,
    Value,
    Model,
    Unit,
    Document,
    callbacks,
    modelsMap,
    Release,
    Organization,
    Contact
)
from openprocurement.ocds.export.helpers import (
    convert_bids,
    create_auction,
    convert_unit_and_location,
    convert_cancellation_and_tenderers,
    convert_questions,
    unique_documents,
    build_package,
    compile_releases
)

extensions = {
    'bids': lambda raw_data: convert_bids(raw_data.get('bids')),
    'auctions': lambda raw_data: create_auction(raw_data),
    'items': lambda raw_data: convert_unit_and_location(raw_data.get('items')),
    'tender': lambda raw_data: convert_cancellation_and_tenderers(raw_data),
    'enquiries': lambda raw_data: convert_questions(raw_data),
    'currentStage': lambda raw_data: raw_data.get('status'),
    'documents': lambda raw_data: unique_documents(raw_data.get('documents'), extension=True),
}


def update_callbacks():
    global callbacks
    global extensions
    callbacks.update(extensions)
    callbacks.pop('tenderers', None)


class TenderExt(Tender):

    __slots__ = Tender.__slots__ + (
        'auctions',
        'tenderID',
        'pendingCancellation',
        'enquiries',
        'lots',
        'procurementMethodType',
        'currentStage',
    )


class AwardExt(Award):

    __slots__ = Award.__slots__ + (
        'lotID',
    )


class ValueExt(Value):

    __slots__ = Value.__slots__ + (
        'valueAddedTaxIncluded',
    )


class Bid(Model):

    __slots__ = (
        'id',
        'date',
        'status',
        'tenderers',
        'value',
        'documents',
        'relatedLot',
        'participationUrl'
    )


class ContractExt(Contract):

    __slots__ = Contract.__slots__ + (
        'suppliers',
        'contractID',
        'contractNumber',
    )


class Auction(Model):

    __slots__ = (
        'url',
        'period',
        'minimalStep',
        'relatedLot',
    )


class UnitExt(Unit):

    __slots__ = Unit.__slots__ + (
        'id',
        'symbol',
        'scheme',
    )


class Location(Model):

    __slots__ = (
        "geomerty",
    )


class ItemExt(Item):

    __slots__ = Item.__slots__ + (
        'deliveryAddress',
        'deliveryLocation',
        'relatedLot',
        'deliveryDate'
    )


class Geometry(Model):

    __slots__ = (
        'coordinates',
    )


class Enquiry(Model):

    __slots__ = (
        'id',
        'date',
        'author',
        'title',
        'description',
        'answer',
        'dateAnswered',
        'relatedItem',
    )


class DocumentExt(Document):

    __slots__ = Document.__slots__ + (
        'relatedItem',
        'documentScope',
    )


class Lot(Model):

    __slots__ = (
        'status',
        'description',
        'title',
        'value',
        'id',
        'pendingCancellation',
    )


class ReleaseExt(Release):

    __slots__ = Release.__slots__ + (
        'bids',
    )


class OrganizationExt(Organization):

    __slots__ = Organization.__slots__ + (
        'additionalContactPoints',
    )


class ContactExt(Contact):

    __slots__ = Contact.__slots__ + (
        'availableLanguage',
    )


class Bids(Model):

    __slots__ = (
        'details',
    )


modelsExt = {
    'contracts': (ContractExt, []),
    'auctions': (Auction, []),
    'tender': (TenderExt, {}),
    'unit': (UnitExt, {}),
    'items': (ItemExt, []),
    'value': (ValueExt, {}),
    'enquiries': (Enquiry, []),
    'lots': (Lot, []),
    'details': (Bid, []),
    'documents': (DocumentExt, []),
    'awards': (AwardExt, []),
    'additionalContactPoints': (ContactExt, []),
    'contactPoint': (ContactExt, {}),
    'tenderers': (OrganizationExt, []),
    'suppliers': (OrganizationExt, []),
    'procuringEntity': (OrganizationExt, {}),
    'buyer': (OrganizationExt, {}),
    'bids': (Bids, {})
}


def update_models_map():
    global modelsMap
    global modelsExt
    modelsMap.update(modelsExt)


def release_tender_ext(tender, prefix):
    release = ReleaseExt(tender, prefix).__export__()
    tag = ['tender']
    for op in ['awards', 'contracts', 'bids']:
        if op in release:
            tag.append(op[:-1])
    release['tag'] = tag
    return release


def release_tenders_ext(tender, prefix):

    def prepare_first_tags(release):
        tag = ['tender']
        for f in ['awards', 'contracts', 'bids']:
            if f in release:
                tag.append(f[:-1])
        return list(set(tag))

    assert 'patches' in tender
    patches = tender.pop('patches')

    first_release = ReleaseExt(tender).__export__()
    first_release['tag'] = prepare_first_tags(first_release)
    releases = [first_release]
    for patch in patches:
        tender = jsonpatch.apply_patch(tender, patch)
        next_release = ReleaseExt(tender).__export__()
        if first_release != next_release:
            diff = jsonpatch.make_patch(first_release, next_release).patch
            tag = []
            for op in diff:
                if op['path'] in ['/tag', '/id']:
                    continue
                if op['op'] != 'add':
                    if not any(p in op['path'] for p in ['awards', 'contracts', 'bids']):
                        tag.append('tenderUpdate')
                    else:
                        for p in ['awards', 'contracts', 'bids']:
                            if p in op['path']:
                                tag.append(p[:-1] + 'Update')
                else:
                    for p in ['awards', 'contracts', 'bids']:
                        if p in op['path']:
                            tag.append(p[:-1])
            next_release['tag'] = list(set(tag))
            releases.append(next_release)
        first_release = next_release
    return releases


def record_tenders_ext(tender, prefix):
    record = {}
    record['releases'] = release_tenders_ext(tender, prefix)
    record['compiledRelease'] = compile_releases(record['releases'])
    record['ocid'] = record['releases'][0]['ocid']
    return record


def package_tenders_ext(tenders, config):
    package = build_package(config)
    releases = []
    for tender in tenders:
        if not tender:
            continue
        if 'patches' in tender:
            releases.extend(release_tenders(tender, config.get('prefix')))
        else:
            releases.append(release_tender_ext(tender, config.get('prefix')))
    package['releases'] = releases
    return package


def package_records_ext(tenders, config):
    package = build_package(config)
    records = []
    for tender in tenders:
        if not tender:
            continue
        records.append(record_tenders_ext(tender, config.get('prefix')))
    package['records'] = records
    return package
