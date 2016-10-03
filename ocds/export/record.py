from .base import Mapping
from .helpers import generate_id, now, get_compiled_release


class Record(Mapping):

    def __init__(self, ocid, releases, publisher, uri):
        super(Record, self).__init__(
            id=generate_id(),
            publishedDate=now().isoformat(),
            releases=releases,
            ocid=ocid,
            compiledRelease=get_compiled_release(releases),
            publisher=publisher,
            uri=uri,
        )
