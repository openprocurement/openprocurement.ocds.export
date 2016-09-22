# -*- coding: utf-8 -*-
from ocds.storage.backends.couch import CouchStorage
import argparse
import yaml
import iso8601
import os
from ocds.export.base import Mapping
from uuid import uuid4


def run():
    parser = argparse.ArgumentParser('API databridge')
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-d', action='append', dest='dates', default=[])
    args = parser.parse_args()
    with open(args.config) as cfg:
        config = yaml.load(cfg)
    storage = CouchStorage(config)
    publisher = {
        "name": "\u0414\u041f \"\u041f\u0440\u043e\u0437\u043e\u0440\u0440\u043e\""
    }
    license = 'https://creativecommons.org/publicdomain/zero/1.0/'
    publicationPolicy = "https://prozorro.gov.ua/publication-policy"
    datestart = iso8601.parse_date(args.dates[0]).isoformat()
    datefinish = iso8601.parse_date(args.dates[1]).isoformat()
    uri = 'https://fake-url/tenders-{}'.format(uuid4().hex)
    data = (storage.get_package(datestart, datefinish, publisher, license, publicationPolicy, uri))
    mapping = Mapping(data)
    if not os.path.exists(config.get('path')):
        os.makedirs(config.get('path'))
    with open('{}/release.json'.format(config.get('path')), 'w') as outfile:
        outfile.write(mapping.to_json())
