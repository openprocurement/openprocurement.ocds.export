import voluptuous


class BaseSchema(voluptuous.Schema):

    def __init__(self, schema, required=False):
        super(BaseSchema, self).__init__(
            schema=schema, required=required, extra=voluptuous.REMOVE_EXTRA)

    def __set__(self, instance, owner):
        try:
            for k, v in self._compiled([], data):
                setattr(instance, k, v)
        except er.MultipleInvalid:
            raise
        except er.Invalid as e:
            raise er.MultipleInvalid([e])

    def __get__(self, instance):
        return instance.value


def value(val):
    try:
        parsed = int(val)
    except ValueError:
        parsed = float(val)
    return parsed


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
        'documents': [document_schema]
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
        'documents': [document_schema]
    }
)


tender = BaseSchema(
    {
        'id': unicode,
        'title': unicode,
        'description': unicode,
        'status': unicode,
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
        'tenderers': [organization_schema],
        'procuringEntity': organization_schema,
        'documents': [document_schema],
    }
)
