# -*- coding: utf-8 -*-
from ocds.storage.backends.couch import CouchStorage
import argparse
import yaml
import iso8601
import os
from ocds.export.package import Package
from ocds.export.release import get_release_from_tender
from uuid import uuid4
import time
import sys


def run():
    parser = argparse.ArgumentParser('Release Packages')
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-d', action='append', dest='dates', default=[])
    parser.add_argument('-n', '--number')
    args = parser.parse_args()
    releases = []
    with open(args.config) as cfg:
        config = yaml.load(cfg)
    storage = CouchStorage(config.get('tenders_db'))
    info = config.get('release')
    uri = 'https://fake-url/tenders-{}'.format(uuid4().hex)
    if args.dates:
        datestart = iso8601.parse_date(args.dates[0]).isoformat()
        datefinish = iso8601.parse_date(args.dates[1]).isoformat()
        for res in storage.get_tenders_between_dates(datestart, datefinish):
            try:
                release = get_release_from_tender(res, info['prefix'])
                releases.append(release)
            except KeyError as e:
                print e
                pass
        data = Package(
            releases,
            info['publisher'],
            info['license'],
            info['publicationPolicy'],
            uri
        )
        if not os.path.exists(config.get('path')):
            os.makedirs(config.get('path'))
        with open('{}/release.json'.format(config.get('path')), 'w') as outfile:
            outfile.write(data.to_json())
    else:
        count = 0
        for row in storage.get_all():
            if row.doc['procurementMethod'] == 'open':
                sys.stdout.write('{}\r'.format(count))
                sys.stdout.flush()
                if 'ТЕСТУВАННЯ'.decode('utf-8') not in row.doc['title']:
                    try:
                        release = get_release_from_tender(row.doc, info['prefix'])
                        releases.append(release)
                        count += 1
                    except KeyError as e:
                        print e
                        pass
                if count == 16384:
                    package = Package(
                        releases,
                        info['publisher'],
                        info['license'],
                        info['publicationPolicy'],
                        uri
                    )
                    releases = []
                    with open('var/report/release-{}.json'.format(time.time()), 'w') as outfile:
                        outfile.write(package.to_json())
                    count = 0
