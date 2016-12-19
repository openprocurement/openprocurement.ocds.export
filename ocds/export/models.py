from datetime import datetime
from uuid import uuid4
from schematics.models import Model
from schematics.types import DateTimeType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import convert, blacklist
from .helpers import get_compiled_release, get_ocid, now, generate_uri
from ocds.export.schema import (
    Tender,
    Award,
    Contract,
    Organization
)



class BaseModel(Model):

    class Options(object):
        serialize_when_none = False


class Publisher(BaseModel):
    name = StringType()


class Release(BaseModel):

    class Options:
        roles = {
            'public': blacklist('procuringEntity')
        }

    # required by standard
    _id = StringType(default=uuid4(), required=True)
    date = StringType(default=now, required=True)
    ocid = StringType(required=True)
    language = StringType(default='uk', required=True)

    # Only one choice. See: http://standard.open-contracting.org/latest/en/schema/codelists/#initiation-type
    initiationType = StringType(default='tender', choices=['tender'], required=True)

    # exported from openprocurement.api data
    procuringEntity = ModelType(Organization, serialized_name="buyer")
    tender = ModelType(Tender)
    awards = ListType(ModelType(Award))
    contracts = ListType(ModelType(Contract))
    
    @serializable(serialize_when_none=False)
    def buyer(self):
        return self.procuringEntity.to_native()

    @serializable(serialize_when_none=False)
    def tag(self):
        tags = []
        if self.tender:
            tags.append('tender')
            if hasattr(self.tender, 'amendment')\
               and getattr(self.tender, 'amendment'):
                tags.append('tenderUpdate')

        for op in ['award', 'contract']:
            field = '{}s'.format(op)
            if getattr(self, field):
                tags.append(op)
                if any([hasattr(i, 'amendment') for i in getattr(self, field, [])
                        if getattr(i, 'amendment')]):
                    tags.append('{}Update'.format(op))
        return tags

    def convert(self, raw_data, **kw):
        if all(f in raw_data for f in self._fields):
            return convert(self.__class__, raw_data, **kw)
        data = {}
        tender = raw_data.get('tender', raw_data)
        if not isinstance(tender, dict):
            tender = dict(tender)

        for f in self._fields:
            value = raw_data.get(f, '') or tender.get(f, '') 
            if value:
                data[f] = value
        data['tender'] = tender
        return convert(self.__class__, data, **kw)

    @serializable(serialize_when_none=False, serialized_name='id')
    def doc_id(self):
        if hasattr(self, '_id'):
            return self._id
        return None


class Record(BaseModel):
    releases = ListType(ModelType(Release))

    @serializable
    def compiledRelease(self):
        return get_compiled_release(self.releases)

    @serializable
    def ocid(self):
        return self.releases[0].ocid


class Package(BaseModel):

    publishedDate = StringType(default=now, required=True)
    publisher = ModelType(Publisher, required=True)
    license = StringType()
    _url = StringType(default=generate_uri)
    _policy_url = StringType()

    @serializable
    def publicationPolicy(self):
        return self._policy_url

    @serializable
    def uri(self):
        return self._url


class ReleasePackage(Package):

    releases = ListType(ModelType(Release), required=True)


class RecordPackage(Package):

    records = ListType(ModelType(Record))
