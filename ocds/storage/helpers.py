import uuid


def get_db_url(user, password, host, port, name=''):
    prefix = ''
    if user:
        prefix = "{}:{}@".format(user, password)
    return "http://{}{}:{}/".format(
        prefix,
        host,
        port,
        name
    )


def generate_ocid(organization_prefix, tender_id):
    return "{}-{}".format(organization_prefix, tender_id)


def generate_id():
    return "{}-{}".format(uuid.uuid4().hex, uuid.uuid4().hex)
