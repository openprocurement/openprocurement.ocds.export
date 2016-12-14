import iso8601
from datetime import datetime
from uuid import uuid4
from schematics.models import Model
from schematics.types import DateTimeType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import convert
from .helpers import get_compiled_release, get_ocid, now
from ocds.export.schema import (
    Tender,
    Award,
    Contract,
    Organization
)



def release_tender(tender, prefix):
    """ returns Release object created from `tender` with ocid `prefix` """
    date = tender.get('dateModified', '')
    ocid = get_ocid(prefix, tender['tenderID'])
    return Release(dict(tender=tender, ocid=ocid, date=date))


def release_tenders(tenders, prefix):
    """ returns list of Release object created from `tenders` with amendment info and ocid `prefix` """
    prev_tender = next(tenders)
    for tender in tenders:
        yield Tender.with_diff(prev_tender, tender)
        prev_tender = tender


class BaseModel(Model):

    class Options(object):
        serialize_when_none = False


class Release(BaseModel):

    # required by standard
    date = StringType(default=now, required=True)
    ocid = StringType(required=True)
    id = StringType(default=uuid4().hex, required=True)
    language = StringType(default='uk', required=True)

    # Only one choice. See: http://standard.open-contracting.org/latest/en/schema/codelists/#initiation-type
    initiationType = StringType(default='tender', choices=['tender'], required=True)

    # exported from openprocurement.api data
    procuringEntity =  ModelType(Organization)
    tender = ModelType(Tender) 
    awards = ListType(ModelType(Award))
    contracts = ListType(ModelType(Contract))
    #planning = ModelType(Organization)

    #@serializable
    #def ocid(self):
    #    return "{}-{}".format(self.prefix, self.tender.tenderID)
    
    @serializable(serialize_when_none=False)
    def buyer(self):
        return self.procuringEntity

    @serializable(serialize_when_none=False)
    def tag(self):
        tags = []
        if self.tender:
            tags.append('tender')
            if hasattr(self.tender, 'amendment') and getattr(self.tender, 'amendment'):
                tags.append('tenderUpdate')

        for op in ['award', 'contract']:
            field = '{}s'.format(op)
            if getattr(self, field):
                tags.append(op)
                if any([hasattr(i, 'amendment') for i in getattr(self, field, [])]):
                    tags.append('{}Update'.format(op))
        return tags

    def convert(self, raw_data, **kw):
        if all(f in raw_data for f in self._fields):
            return convert(self.__class__, raw_data, **kw)
        data = {}
        if not 'tender' in data:
            data['tender'] = raw_data

        for f in self._fields:
            if f in raw_data:
                data[f] = raw_data.pop(f, data['tender'].pop(f, ''))
        return convert(self.__class__, data, **kw)


class Record(BaseModel):
    releases=ListType(ModelType(Release))

    @serializable
    def compiledRelease(self):
        return get_compiled_release(self.releases)

    @serializable
    def ocid(self):
        return self.releases[0].ocid



class Package(BaseModel):

    publishedDate = DateTimeType(default=datetime.now, required=True)
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
