import jsonpatch
from jsonpointer import resolve_pointer
from .helpers import (
    now,
    generate_id,
)
from .base import Mapping
from .helpers import parse_tender, get_tags_from_tender, get_ocid, get_tag


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
    return Release(get_ocid(prefix, tender['tenderID']), tags, get_tag(tags), date)


def additional_release_info(patch):
    tags = []
    for _tag in ['award', 'contract']:
        for op in patch['changes']:
            if _tag in op['path']:
                if op['op'] == 'add':
                    tags.append(_tag)
                else:
                    tags.append('{}Update'.format(_tag))
            else:
                tags.append('tenderUpdate')
    return list(set(tags))


def release_tenders(tenders, prefix):
    tender = next(tenders)
    yield release_tender(tender, prefix)
    prev_tender = tender
    for tender in tenders:
        patch = jsonpatch.create_patch(prev_tender, tender)
        if path:
            release = release_tender(tender, prefix)
            additional_release_info(release, patch)
            yield release
