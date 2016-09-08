from .helpers import (
    now,
    generate_id,
)
from .schema import release
from .base import Mapping


class Release(Mapping):

    __schema__ = release

    def __init__(self, ocid, tags, date=None):
        super(Release, self).__init__(
            language='uk',
            ocid='ocid',
            id=generate_id(),
            date=now().isoformat(),
            tag=map(lambda t: t.__tag__ for t in tags),
        )

        for _tag in tags:
            if isinstance(_tag, list):
                setattr(self, _tag[0].__tag__, _tag)
            elif isinstance(_tag, Mapping):
                setattr(self, _tag.__tag__, _tag)
