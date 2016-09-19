from .helpers import (
    now,
    generate_id,
)
from .base import Mapping
from .helpers import parse_tender, get_tags_from_tender, get_ocid


class Release(Mapping):

    def __init__(self, ocid, tags, date=None):
        if not date:
            date = now().isoformat()
        super(Release, self).__init__(
            language='uk',
            ocid='ocid',
            id=generate_id(),
            date=date,
            tag=map(lambda t: t.__tag__ , tags),
        )

        for _tag in tags:
            if isinstance(_tag, list):
                setattr(self, _tag[0].__tag__, _tag)
            elif isinstance(_tag, Mapping):
                setattr(self, _tag.__tag__, _tag)


def get_release_from_tender(tender, prefix):
    date = tender['dateModified']
    return Release(
        get_ocid(prefix, tender['tenderID']),
        get_tags_from_tender(parse_tender(tender)),
        date
    )
