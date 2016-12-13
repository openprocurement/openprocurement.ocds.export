import iso8601
from datetime import datetime
from uuid import uuid4
from schematics.models import Model
from schematics.types import DateTimeType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import convert
from .helpers import get_compiled_release
from ocds.export.schema import (
    Tender,
    Award,
    Contract,
    Organization
)


class BaseModel(Model):

    class Options(object):
        serialize_when_none = False


class Release(BaseModel):

    # required by standard
    date = DateTimeType(default=datetime.now, required=True)
    ocid = StringType(required=True)
    id = StringType(default=uuid4().hex, required=True)
    language = StringType(default='uk')

    # Only one choice. See: http://standard.open-contracting.org/latest/en/schema/codelists/#initiation-type
    initiationType = StringType(default='tender', choices=['tender'], required=True)

    # exported from openprocurement.api data
    buyer =  ModelType(Organization)
    tender = ModelType(Tender) 
    awards = ListType(ModelType(Award))
    contracts = ListType(ModelType(Contract))
    #planning = ModelType(Organization)

    @serializable
    def tag(self):
        tags = []
        if self.tender:
            tags.append('tender')
            if hasattr(self.tender, 'amendment'):
                tags.append('tenderUpdate')

        for op in ['award', 'contract']:
            field = '{}s'.format(op)
            if getattr(self, field):
                tags.append(op)
                if any([hasattr(i, 'amendment') for i in getattr(self, field, [])]):
                    tags.append('{}Update'.format(op))
        return tags

    def convert(self, raw_data, context=None, **kw):
        data = {}
        data['tender'] = Tender(raw_data)

        if 'awards' in raw_data:
            data['awards'] = [Award(A) for A in raw_data['awards']]
        if 'contracts' in raw_data:
            data['contracts'] = [Contract(A) for A in raw_data['contracts']]

        return convert(self.__class__, data, context=context, **kw)


class Record(BaseModel):
    ocid = StringType()
    releases=ListType(ModelType(Release))

    @serializable
    def compiledRelease(self):
        return get_compiled_release(self.releases)


class Package(BaseModel):

    publishedDate = DateTimeType(default=lambda: datetime.now, required=True)
    publisher = StringType(required=True)
    license = StringType()
    _url = StringType()
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
