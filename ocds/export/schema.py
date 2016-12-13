import voluptuous
from itertools import groupby
from schematics.models import Model
from schematics.types import BaseType, StringType, FloatType, IntType
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import convert
from .helpers import tender_converter, unique_tenderers, unique_documents


# TODO: Unique tenderers and documents
# TODO: Import loop(parse_tender)
# DONE: tender statuses


class BaseModel(Model):

    class Options(object):
        serialize_when_none = False

    def convert(self, raw_data, context=None, **kw):
        kw['strict'] = False
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

class Award(BaseModel):
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

    @serializable
    def numberOfTenderers(self):
        return len(self.tenderers) if self.tenderers else 0

    def convert(self, raw_data, context=None, **kw):
        data = tender_converter(raw_data)
        data['tenderers'] = unique_tenderers(data['tenderers']) 
        if 'documents' in data:
            unique_documents(data['documents'])
        return super(Tender, self).convert(data, context=context, **kw)
