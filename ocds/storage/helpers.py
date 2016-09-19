import yaml
import os
import json
import uuid
basepath = '/data/dimon.obert/ocds.storagemyver/tests'


def get_db_url(config):
    db_config = config['db']
    prefix = "{}:{}".format(db_config['admin']['user'], db_config['admin']['password'])
    return "http://{}@{}:{}".format(
        prefix,
        db_config['net']['host'],
        db_config['net']['port']
    )


def generate_ocid(tender_id):
    return "ocid-32d4gz-fake-{}".format(tender_id)


def get_config_from_file(file_name):
    with open(os.path.join(basepath, '{}'.format(file_name))) as stream:
        return yaml.load(stream)


def get_release_from_file(file_name):
    with open('/data/dimon.obert/ocds.storagemyver/releases/{}'.format(file_name)) as stream:
        return json.load(stream)


def generate_id():
    return "{}-{}".format(uuid.uuid4().hex, uuid.uuid4().hex)