import jsonpatch
from itertools import groupby
from datetime import datetime
from schematics.models import Model
from schematics.types import BaseType, StringType, FloatType, IntType, DateTimeType
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import convert
from .helpers import tender_converter, unique_tenderers, unique_documents, patch_converter


# TODO: Unique tenderers and documents
# TODO: Import loop(parse_tender)
# DONE: tender statuses

def now():
    return datetime.now().isoformat()


class BaseModel(Model):

    class Options(object):
        serialize_when_none = False

    def convert(self, raw_data, context=None, **kw):
        kw['strict'] = False
        if 'documents' in raw_data:
            unique_documents(raw_data['documents'])
        return convert(self.__class__, raw_data, context=context, **kw)


class Status(BaseType):

    """Only active status in standard"""

    def to_native(self, value):
        return value.split('.')[0]


class Identifier(BaseModel):

    scheme = StringType()
    id = StringType()
    legalName = StringType()
    uri = StringType()


class Document(BaseModel):

    id = StringType()
    documentType = StringType()
    title = StringType()
    description = StringType()
    url = StringType()
    datePublished = StringType()
    dateModified = StringType()
    format = StringType()
    language = StringType()


class Classification(BaseModel):

    scheme = StringType()
    id = StringType()
    description = StringType()
    uri = StringType()


class Period(BaseModel):

    startDate = StringType()
    endDate = StringType()


class Value(BaseModel):

    amount = FloatType()
    currency = StringType()


class Unit(BaseModel):

    name = StringType()
    value = ModelType(Value)


class Address(BaseModel):

    streetAddress = StringType()
    locality = StringType()
    postalCode = StringType()
    countryName = StringType()


class Contact(BaseModel):

    name = StringType()
    email = StringType()
    telephone = StringType()
    faxNumber = StringType()
    url = StringType()


class Organization(BaseModel):

    identifier = ModelType(Identifier) 
    additionalIdentifiers = ListType(ModelType(Identifier))
    name = StringType()
    address = ModelType(Address)
    contactPoint = ModelType(Contact)


class Item(BaseModel):

    id = StringType()
    description = StringType()
    classification = ModelType(Classification)
    additionalClassifications = ListType(ModelType(Classification))
    quantity = IntType()
    unit = ModelType(Unit)


class Change(BaseModel):
    property = StringType()
    former_value = StringType()


class Amendment(BaseModel):

    date = StringType(default=now)
    changes = ListType(ModelType(Change))
    rationale = StringType()


class Award(BaseModel):
    """See: http://standard.open-contracting.org/latest/en/schema/reference/#award"""

    id = StringType()
    title = StringType()
    description = StringType()
    status = StringType(choices=['pending', 'active', 'unsuccessful', 'cancelled'])
    date = StringType()
    value = ModelType(Value)
    suppliers = ListType(ModelType(Organization)) 
    items = ListType(ModelType(Item))
    contractPeriod = ModelType(Period)
    documents = ListType(ModelType(Document))


class Contract(BaseModel):
    """See: http://standard.open-contracting.org/latest/en/schema/reference/#contract"""

    id = StringType()
    awardID = StringType()
    title = StringType()
    description = StringType()
    status = StringType(choices=['pending', 'active', 'cancelled', 'terminated'])
    period = ModelType(Period)
    value = ModelType(Value) 
    items = ListType(ModelType(Item)) 
    dateSigned = StringType()
    documents = ListType(ModelType(Document))


class Tender(BaseModel):
    """See: http://standard.open-contracting.org/latest/en/schema/reference/#tender"""

    id = StringType()
    title = StringType()
    description = StringType()
    status = Status()
    items = ListType(ModelType(Item)) 
    minValue = ModelType(Item) 
    value = ModelType(Value) 
    procurementMethod = StringType()
    procurementMethodRationale = StringType()
    awardCriteria = StringType()
    awardCriteriaDetails = StringType()
    submissionMethod = ListType(StringType)
    submissionMethodDetails = StringType()
    tenderPeriod = ModelType(Period) 
    enquiryPeriod = ModelType(Period)
    hasEnquiries = StringType()
    eligibilityCriteria = StringType()
    awardPeriod = ModelType(Period)
    tenderers = ListType(ModelType(Organization))
    procuringEntity = ModelType(Organization)
    documents = ListType(ModelType(Document)) 
    amendment = ModelType(Amendment)

    @serializable
    def numberOfTenderers(self):
        return len(self.tenderers) if self.tenderers else 0

    def convert(self, raw_data, context=None, **kw):
        data = tender_converter(raw_data)
        data['tenderers'] = unique_tenderers(data['tenderers']) 
        return super(Tender, self).convert(data, context=context, **kw)
    
    @classmethod
    def with_diff(cls, prev_tender, new_tender):
        amendment = {}
        patch = jsonpatch.make_patch(tender_converter(new_tender), tender_converter(prev_tender)).patch
        if patch:
            amendment['changes'] = patch_converter(patch)
            amendment['date'] = new_tender['dateModified']
        new_tender['amendment'] = amendment
        return cls(new_tender)
