import voluptuous
from itertools import groupby


class BaseSchema(voluptuous.Schema):

    def __init__(self, schema, required=False):
        super(BaseSchema, self).__init__(
            schema=schema, required=required, extra=voluptuous.REMOVE_EXTRA)


def value(val):
    try:
        parsed = int(val)
    except ValueError:
        parsed = float(val)
    return parsed


def tender_status(status):
    if status not in ['complete', 'unsuccessful', 'cancelled']:
        return 'active'
    return status


def unique_tenderers(tenderers):
    tenderers = [{t['identifier']['id']: t} for t in tenderers]
    if tenderers:
        res = [t.values() for t in tenderers][0]
        return res
    return []


def unique_documents(documents):
    temp = documents
    count = 0
    list_a = sorted([doc['id'] for doc in documents])
    result = dict([(r, len(list(grp))) for r, grp in groupby(list_a)])
    for i in temp:
        if result[i['id']] > 1:
            i['id'] = i['id'] + '-{}'.format(count)
            count += 1
    return [document_schema(t) for t in temp]


identifier_schema = BaseSchema(
    {
        'scheme': unicode,
        'id': unicode,
        'legalName': unicode,
        'uri': unicode
    }
)


document_schema = BaseSchema(
    {
        'id': unicode,
        'documentType': unicode,
        'title': unicode,
        'description': unicode,
        'url': unicode,
        'datePublished': unicode,
        'dateModified': unicode,
        'format': unicode,
        'language': unicode,
    },
)


classification_schema = BaseSchema(
    {
        'scheme': unicode,
        'id': unicode,
        'description': unicode,
        'uri': unicode
    }
)


period_schema = BaseSchema(
    {
        'startDate': unicode,
        'endDate': unicode
    }
)


value_schema = BaseSchema(
    {
        'amount': value,
        'currency': unicode
    }
)


unit_schema = BaseSchema(
    {
        'name': unicode,
        'value': value_schema
    }
)


address_schema = BaseSchema({
    'streetAddress': unicode,
    'locality': unicode,
    'postalCode': unicode,
    'countryName': unicode
})


contact_point_schema = BaseSchema(
    {
        'name': unicode,
        'email': unicode,
        'telephone': unicode,
        'faxNumber': unicode,
        'url': unicode
    }
)


organization_schema = BaseSchema(
    {
        'identifier': identifier_schema,
        'additionalIdentifiers': identifier_schema,
        'name': unicode,
        'address': address_schema,
        'contactPoint': contact_point_schema
    }
)


items_schema = BaseSchema(
    {
        'id': unicode,
        'description': unicode,
        'classification': classification_schema,
        'additionalClassifications': [classification_schema],
        'quantity': value,
        'unit': unit_schema
    }
)


award = BaseSchema(
    {
        'id': unicode,
        'title': unicode,
        'description': unicode,
        'status': unicode,
        'date': unicode,
        'value': value_schema,
        'suppliers': [organization_schema],
        'items': [items_schema],
        'contractPeriod': period_schema,
        'documents': (unique_documents)
    }
)

contract = BaseSchema(
    {
        'id': unicode,
        'awardID': unicode,
        'title': unicode,
        'description': unicode,
        'status': unicode,
        'period': period_schema,
        'value': value_schema,
        'items': [items_schema],
        'dateSigned': unicode,
        'documents': unique_documents
    }
)


tender = BaseSchema(
    {
        'id': unicode,
        'title': unicode,
        'description': unicode,
        'status': tender_status,
        'items': [items_schema],
        'minValue': value_schema,
        'value': value_schema,
        'procurementMethod': unicode,
        'procurementMethodRationale': unicode,
        'awardCriteria': unicode,
        'awardCriteriaDetails': unicode,
        'submissionMethod': [unicode],
        'submissionMethodDetails': unicode,
        'tenderPeriod': period_schema,
        'enquiryPeriod': period_schema,
        'hasEnquiries': unicode,
        'eligibilityCriteria': unicode,
        'awardPeriod': period_schema,
        'numberOfTenderers': value,
        'tenderers': unique_tenderers,
        'procuringEntity': organization_schema,
        'documents': unique_documents,
    }
)


release = BaseSchema(
    {
        'language': str,
        'ocid': str,
        'date': str,
        'tag': list,
        'tags': list,
        'buyer': organization_schema,
        'tender': tender,
        'awards': [award],
        'contract': [contract]
    }
)
