# -*- coding: utf-8 -*-
import argparse
import os
import logging
import couchdb.json
import zipfile
import boto3

from functools import partial
from itertools import izip_longest as zip_longest
from simplejson import dump, dumps
from gevent import spawn, sleep

from os.path import join
from gevent import spawn, sleep, joinall, monkey as M
from gevent.queue import Queue
from gevent.event import Event

from jinja2 import Environment, PackageLoader 
from openprocurement.ocds.export.storage import TendersStorage, ContractsStorage
from openprocurement.ocds.export.models import package_tenders, package_records,\
    callbacks, modelsMap
from openprocurement.ocds.export.ext.models import (
    package_tenders_ext,
    package_records_ext,
    update_callbacks,
    update_models_map
)
from openprocurement.ocds.export.helpers import (
    connect_bucket,
    read_config,
    parse_dates,
    make_zip,
    dump_json,
    fetch_ids,
    create_html,
    update_index,
    parse_args,
    connect_bucket
)
logging.getLogger('boto').setLevel(logging.WARN)
logging.getLogger('boto3').setLevel(logging.WARN)
logging.getLogger('botocore').setLevel(logging.WARN)
couchdb.json.use('simplejson')


ENV = Environment(
    loader=PackageLoader('openprocurement.ocds.export', 'templates'),
    trim_blocks=True
)
LOGGER = logging.getLogger(__name__)
REGISTRY = {
    "max_date": None,
    "bucket": None,
    "contracting": False,
    'tenders_storage': None,
    "record": False,
    "config": {},
    "db": None,
    "contracts_storage": None,
    'can_url': 'http://{}/merged_{}/{}',
    'ext_url': 'http://{}/merged_with_extensions_{}/{}',
    'zip_path': '',
    'zipq': Queue(),
    'zipq_ext': Queue(),
    'done': Event(),
    'archives': Queue(),
}
REGISTRY['package_funcs'] = [package_records, package_records_ext] if REGISTRY['record']\
                            else  [package_tenders, package_tenders_ext]


def dump_json_to_s3(name, data, pretty=False):
    LOGGER.info('Upload {} to s3 bucket'.format(name))
    time = REGISTRY['max_date']

    dir_name = 'merged_with_extensions_{}/{}'.format(time, name) if\
               'extensions' in data['uri'] else 'merged_{}/{}'.format(time, name)
    try:
        if pretty:
            REGISTRY['bucket'].put_object(Key=dir_name, Body=dumps(data, indent=4))
        else:
            REGISTRY['bucket'].put_object(Key=dir_name, Body=dumps(data))
        del data
        LOGGER.info("Successfully uploaded {}".format(name))
    except Exception as e:
        LOGGER.fatal("Exception duting upload {}".format(e))


def zip_package(name, data):
    zip_path = REGISTRY['zip_path'] if not 'ext' in data['uri'] else REGISTRY['zip_path_ext']
    full_path = join(zip_path, 'releases.zip')
    dir_name = 'merged_with_extensions_{}/releases.zip'.format(REGISTRY['max_date']) if\
               'ext' in zip_path else 'merged_{}/releases.zip'.format(REGISTRY['max_date'])

    with zipfile.ZipFile(full_path, 'a', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        if not isinstance(data, (str, unicode)):
            data = dumps(data)
        try:
            zf.writestr(name, data)
            LOGGER.info("{} written to atchive {}".format(name, full_path))
            del data
        except Exception as e:
            LOGGER.fatal("Unable to write package {} to archive {}".format(name, full_path))


def upload_archives():
    LOGGER.info('Start uploading archives')
    dirs = [
        'merged_{}/releases.zip'.format(REGISTRY['max_date']),
        'merged_with_extensions_{}/releases.zip'.format(REGISTRY['max_date'])
    ]

    paths = [
        join(REGISTRY['zip_path'], 'releases.zip'),
        join(REGISTRY['zip_path_ext'], 'releases.zip'),
    ]
    g = []
    for path, name in zip(paths, dirs):
        g.append(spawn(REGISTRY['bucket'].upload_file(path, name)))
    joinall(g)


def fetch_and_dump(params):
    nth, (start, end) = params
    LOGGER.info('Start packaging {}th package! Params: startdoc={},'
                ' enddoc={}'.format(nth, start, end))
    if not start and not end:
        return

    args = {'startkey': start}
    if end:
        args.update(dict(endkey=end))

    if REGISTRY['contracting']:
        args.update({'contract_storage': REGISTRY['contracts_storage']})

    result = [tender for tender in REGISTRY['tenders_storage'].get_tenders(**args)]

    name = 'record-{0:07d}.json'.format(nth) if REGISTRY['record'] else 'release-{0:07d}.json'.format(nth)
    max_date = REGISTRY['max_date']
    try:

        for pack, params in zip(REGISTRY['package_funcs'],
            [{'uri': REGISTRY['can_url'],
              'models': modelsMap,
              'callbacks': callbacks,
              'q': REGISTRY['zipq']},
             {'uri': REGISTRY['ext_url'],
              'models': update_models_map(),
              'callbacks': update_callbacks(),
              'q': REGISTRY['zipq_ext']}]):
            LOGGER.info("Start package: {}".format(pack.__name__))
            package = pack(result[:-1], params['models'], params['callbacks'], REGISTRY['config'].get('release'))
            package['uri'] = params['uri'].format(REGISTRY['bucket'].name, max_date, name)
            if nth == 1:
                pretty_package = pack(result[:24], params['models'], params['callbacks'], REGISTRY['config'].get('release'))
                pretty_package['uri'] = params['uri'].format(REGISTRY['bucket'], max_date, 'example.json')
                dump_json_to_s3('example.json', pretty_package, pretty=True)

            dump_json_to_s3(name, package)
            zip_package(name, package)
            del package
        del result
    except Exception as e:
        LOGGER.info('Error: {}'.format(e))
        return

    LOGGER.info('Done {}th package! Params: startdoc={}, enddoc={}'.format(nth, start, end))


def run():
    args = parse_args()
    config = read_config(args.config)
    REGISTRY['config'] =  config
    REGISTRY['bucket'] = boto3.resource('s3').Bucket(config['bucket'])

    REGISTRY['tenders_storage'] = TendersStorage(config['tenders_db']['url'],
                                                 config['tenders_db']['name'])
    REGISTRY['db'] = REGISTRY['tenders_storage']
    LOGGER.info('Start packaging')
    REGISTRY['record'] = args.rec
    REGISTRY['contracting'] = args.contracting
    REGISTRY['zip_path'] = config['path_can']
    REGISTRY['zip_path_ext'] = config['path_ext']
    nam = 'records' if args.rec else 'releases'

    if args.dates:
        datestart, datefinish = parse_dates(args.dates)
        to_release = REGISTRY['tenders_storage'].get_between_dates(datestart, datefinish)
        if args.rec:
            package_func = package_records_ext if args.ext else package_records
        else:
            package_func = package_tenders_ext if args.ext else package_tenders
        pack = package_func(list(to_release), config)
        name = '{}_between_{}_{}'.format(nam,
                                         datestart.split('T')[0],
                                         datefinish.split('T')[0])
        with open(os.path.join(config['path'], name, 'w')) as stream:
            dump(pack, stream)
    else:
        for archive in [REGISTRY['zip_path'], REGISTRY['zip_path_ext']]:
            path = os.path.join(archive, 'releases.zip')
            if os.path.exists(path):
                os.remove(path)
        max_date = REGISTRY['tenders_storage'].get_max_date().split('T')[0]
        REGISTRY['max_date'] = max_date
        total = int(args.number) if args.number else 4096
        key_ids = fetch_ids(REGISTRY['tenders_storage'], total)
        LOGGER.info('Fetched key doc ids')

        params = enumerate(
            zip_longest(key_ids, key_ids[1::], fillvalue=''),
            1
        )
        sleep(1)
        LOGGER.info("Start working")
        map(fetch_and_dump, params)

        upload_archives()
        bucket = connect_bucket(config)
        update_index(ENV, bucket)
