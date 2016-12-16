from .models import (
    Release,
    ReleasePackage,
    Record,
    RecordPackage
)
from .schema import Tender
from .helpers import (
    mode_test,
    get_ocid
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
