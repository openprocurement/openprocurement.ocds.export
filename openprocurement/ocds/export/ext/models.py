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
    Contact,
    Period
)
from openprocurement.ocds.export.helpers import (
    convert_bids,
    create_auction,
    convert_unit_and_location,
    convert_cancellation,
    convert_questions,
    unique_documents,
    build_package,
)

extensions = {
    'bids': lambda raw_data: convert_bids(raw_data.get('bids')),
    'auctions': lambda raw_data: create_auction(raw_data),
    'items': lambda raw_data: convert_unit_and_location(raw_data.get('items')),
    'tender': lambda raw_data: convert_cancellation(raw_data),
    'enquiries': lambda raw_data: convert_questions(raw_data),
    'currentStage': lambda raw_data: raw_data.get('status'),
    'documents': lambda raw_data: unique_documents(raw_data.get('documents'), extension=True),
}


def update_callbacks():
    global callbacks
    global extensions
    callbacks.update(extensions)


class TenderExt(Tender):

    __slots__ = Tender.__slots__ + (
        'auctions',
        'tenderID',
        'pendingCancellation',
        'enquiries',
        'lots',
        'procurementMethodType',
        'currentStage',
        'qualifications',
        'qualificationPeriod',
        'guarantee',
        'complaints',
        'complaintPeriod',
        'features',
        'shortlistedFirms',
        'cause',
        'causeDescription',
        'stage2TenderID',
    )


class AwardExt(Award):

    __slots__ = Award.__slots__ + (
        'lotID',
        'qualified',
        'complaints',
        'complaintPeriod',
        'eligible',
        'subcontractingDetails'
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
        'participationUrl',
        'selfQualified',
        'selfEligible',
        'subcontractingDetails',
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
        'guarantee'
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


class Qualification(Model):

    __slots__ = (
        'status',
        'lotID',
        'description',
        'title',
        'eligible',
        'id',
        'qualified',
        'bidID',
        'date',
        'documents'
    )


class Guarantee(Model):

    __slots__ = (
        'amount',
        'currency'
    )


class Complaint(Model):

    __slots__ = (
        'status',
        'tendererActionDate',
        'satisfied',
        'tendererAction',
        'dateSubmitted',
        'id',
        'reviewPlace',
        'documents',
        'title',
        'decision',
        'acceptance',
        'dateEscalated',
        'rejectReasonDescription',
        'cancellationReason',
        'dateAnswered',
        'type',
        'relatedLot',
        'description',
        'dateCancelled',
        'date',
        'dateDecision',
        'author',
        'rejectReason',
        'resolutionType',
        'resolution',
        'reviewDate'
    )


class Feature(Model):

    __slots__ = (
        'code',
        'featureOf',
        'relatedItem',
        'title',
        'description',
        'enum'
    )


class ShortlistedFirm(Model):

    __slots__ = (
        'lots',
        'identifier',
        'name',
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
    'bids': (Bids, {}),
    'qualifications': (Qualification, []),
    'qualificationPeriod': (Period, {}),
    'guarantee': (Guarantee, {}),
    'complaints': (Complaint, []),
    'complaintPeriod': (Period, {}),
    'features': (Feature, []),
    'shortlistedFirms': (ShortlistedFirm, [])
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


def package_tenders_ext(tenders, config):
    update_models_map()
    update_callbacks()
    package = build_package(config)
    package['releases'] = [release_tender_ext(
        t, config.get('prefix')) for t in tenders]
    return package
