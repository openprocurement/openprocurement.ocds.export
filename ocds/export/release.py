from .helpers import (
    get_ocid,
    get_tags_from_tender,
    now,
    generate_id,
)
from .tag import Mapping


class BaseRelease(object):

    def __init__(self, ocid, tags, date=None):

        self.language = 'uk'
        self.ocid = ocid
        self.id = generate_id()
        if not date:
            date = now().isoformat()
        self.date = date
        self.tag = map(lambda t: t.__tag__ for t in tags)
        self.initiationType = 'tender'
        for _tag in tags:
            if isinstance(_tag, list):
                setattr(self, _tag[0].__tag__, _tag)
            elif isinstance(_tag, Mapping):
                setattr(self, _tag.__tag__, _tag)

    def serialize(self):
        return self.__dict__


class TenderRelease(BaseRelease):

    def __init__(self, prefix, tender):
        tags = get_tags_from_tender(tender)
        ocid = get_ocid(prefix, tender['tenderID'])
        super(self, TenderRelease).__init__(ocid, tags, tender['dateModified'])


def generate_release(tender):
    pass


def generate_update_release(prev_ver, curr_ver, tag='tender'):
    pass
