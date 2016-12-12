from .helpers import (
    now,
    generate_id,
)
from .base import Mapping
from .helpers import get_tags_from_tender, get_ocid, make_tags, parse_tender
import jsonpatch as jpatch


class Release(Mapping):

    def __init__(self, ocid, tags, tag, date=None):
        if not date:
            date = now().isoformat()
        super(Release, self).__init__(
            language='uk',
            ocid=ocid,
            id=generate_id(),
            date=date,
            tag=tag,
            initiationType='tender',
        )

        for _tag in tags:
            if isinstance(_tag, list):
                setattr(self, _tag[0].__tag__, _tag)
            elif isinstance(_tag, Mapping):
                setattr(self, _tag.__tag__, _tag)


def release_tender(tender, prefix):
    date = tender['dateModified']
    tags = get_tags_from_tender(parse_tender(tender))
    return Release(
        get_ocid(prefix, tender['tenderID']),
        tags,
        date
    )


def release_tenders(tenders, prefix):
    prev_tender = next(tenders)
    first_rel = release_tender(prev_tender, prefix)
    first_rel['tag'] = ['tender']
    yield first_rel
    for tender in tenders:
        patch = jpatch.make_patch(prev_tender, tender)
        release = release_tender(tender, prefix)
        release['tag'] = list(make_tags(patch))
        prev_tender = tender
        yield release
