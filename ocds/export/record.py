from .base import Mapping
from .helpers import now, generate_uri, get_compiled_release


class Record(Mapping):

    def __init__(self, releases, ocid):
        super(Record, self).__init__(
            ocid=ocid,
            releases=releases,
            compiledRelease=get_compiled_release(releases)
        )


class Record_Package(Mapping):

    def __init__(self,
                 records,
                 publisher,
                 license,
                 publicationPolicy):
        super(Record_Package, self).__init__(
            records=records,
            publicationPolicy=publicationPolicy,
            publisher=publisher,
            license=license,
            uri=generate_uri(),
            publishedDate=now().isoformat(),
        )
