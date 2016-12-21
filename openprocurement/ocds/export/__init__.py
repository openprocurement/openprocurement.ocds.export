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
        data = {}
        for field in ['tender', 'awards', 'contracts']:
            model = getattr(Release, field).model_class
            if field in tender:
                data[field] = model.fromDiff(prev_tender.get(field, ''), tender.get(field, ''))
            elif field == 'tender':
                data['tender'] = model.fromDiff(prev_tender, tender)
        yield Release(data)
        prev_tender = tender


def package_tenders(tenders, params):
    data = {}
    for field in ReleasePackage._fields:
        if field in params:
            data[field] = params.get(field, '')
    data['releases'] = [release_tender(tender, params.get('prefix')) for tender in tenders]
    return ReleasePackage(dict(**data)).serialize()
