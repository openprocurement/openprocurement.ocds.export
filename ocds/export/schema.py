import jsonpatch
from urllib import quote
from urlparse import urlparse, urlunparse
from schematics.models import Model
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import convert
from schematics.types import (
    BaseType,
    StringType,
    FloatType,
    IntType,
)
from .helpers import (
    tender_converter,
    unique_tenderers,
    unique_documents,
    patch_converter,
    now
)
from .convert import Converter


invalidsymbols = ["`","~","!", "@","#","$", '"']


class BaseModel(Model):

    class Options(object):
        serialize_when_none = False

    def convert(self, raw_data, strict=False, **kw):
        if 'documents' in raw_data:
            unique_documents(raw_data['documents'])
        return convert(self.__class__, raw_data, strict=False, **kw)


class Status(BaseType):
    """Only active status in standard"""

    def to_native(self, value):
        return value.split('.')[0]


class Url(BaseType):
    """Fixes invalid urls in validator"""

    def to_native(self, value, **kw):
        return ''.join(c for c in value.encode('ascii','ignore') if c not in invalidsymbols)


class Identifier(BaseModel):

    scheme = StringType()
    id = StringType()
    legalName = StringType()
    uri = Url()


class Document(BaseModel):

    id = StringType()
    documentType = StringType()
    title = StringType()
    description = StringType()
    url = Url()
    datePublished = StringType()
    dateModified = StringType()
    format = StringType()
    language = StringType()


class Classification(BaseModel):

    scheme = StringType()
    id = StringType()
    description = StringType()
    # uri = StringType()
    uri = Url() 


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
    url = Url()


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
    former_value = BaseType()


class Amendment(BaseModel):

    date = StringType(default=now)
    changes = ListType(ModelType(Change))
    rationale = StringType()


class Award(BaseModel, Converter):
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
    amendment = ModelType(Amendment)


class Contract(BaseModel, Converter):
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
    amendment = ModelType(Amendment)
    

class Tender(BaseModel, Converter):
    """See: http://standard.open-contracting.org/latest/en/schema/reference/#tender"""

    _id = StringType()
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
    
    @serializable(serialized_name='id')
    def tender_id(self):
        return self._id 

    @serializable
    def numberOfTenderers(self):
        return len(self.tenderers) if self.tenderers else 0
    
    @classmethod
    def _convert(cls, raw_data):
        return cls(raw_data).serialize()

    def convert(self, raw_data, **kw):
        return super(Tender, self).convert(tender_converter(raw_data), **kw)
