from .base import Mapping
from .helpers import now


class Package(Mapping):

    def __init__(
        self,
        releases,
        publisher,
        license,
        publicationPolicy,
        uri
    ):
        super(Package, self).__init__(
            publishedDate=now().isoformat(),
            releases=releases,
            publisher=publisher,
            license=license,
            publicationPolicy=publicationPolicy,
            uri=uri
        )
