# -*- coding: utf-8 -*-
import argparse
import os
import logging
import couchdb.json
import multiprocessing as mp
from functools import partial
from itertools import izip_longest as zip_longest
from simplejson import dump
from jinja2 import (
    Environment,
    PackageLoader
)

from openprocurement.ocds.export.storage import (
    TendersStorage,
    ContractsStorage
)
from openprocurement.ocds.export.models import (
    package_tenders,
    package_records,
    callbacks,
    modelsMap
)
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
    put_to_s3,
    create_html,
    update_index
)

couchdb.json.use('simplejson')
logger = logging.getLogger('packer')
ENV = Environment(
    loader=PackageLoader('openprocurement.ocds.export', 'templates'),
    trim_blocks=True
)


def parse_args():
    parser = argparse.ArgumentParser('Release Packages')
    parser.add_argument('-c', '--config',
                        required=True,
                        help="Path to configuration file")
    parser.add_argument('-d', action='append',
                        dest='dates',
                        default=[],
                        help='Start-end dates to generate package')
    parser.add_argument('-n', '--number')
    parser.add_argument('-r', '--records',
                        action='store_true',
                        default=False,
                        help='Generate record too')
    parser.add_argument('-s3',
                        action='store_true',
                        help="Choose to start uploading to aws s3",
                        default=False)
    parser.add_argument('-rec',
                        action='store_true',
                        help='Choose to start dump record packages',
                        default=False)
    parser.add_argument('-contracting',
                        action='store_true',
                        help='Choose to include contracting',
                        default=False)
    return parser.parse_args()


def fetch_and_dump(config, max_date, params, record=False, contracting=False):
    nth, (start, end) = params
    logger.info('Start {}th dump startdoc={}'
                ' enddoc={}'.format(nth, start, end))
    db = TendersStorage(config['tenders_db']['url'],
                        config['tenders_db']['name'])
    bucket = config.get('bucket')
    if not start and not end:
        return
    args = {
        'startkey': start
    }
    if end:
        args.update(dict(endkey=end))
    if contracting:
        contract = ContractsStorage(config['contracts_db']['url'],
                        config['contracts_db']['name'])
        args.update(dict(contract_storage=contract))
        result = [tender for tender in db.get_tenders(**args)]
    else:
        result = [tender for tender in db.get_tenders(**args)]
    if record:
        package_funcs = [package_records, package_records_ext]
    else:
        package_funcs = [package_tenders, package_tenders_ext]
    can_url = 'http://{}/merged_{}/{}'
    ext_url = 'http://{}/merged_with_extensions_{}/{}'
    name = 'record-{0:07d}.json'.format(nth) if record else 'release-{0:07d}.json'.format(nth)
    path_can = config['path_can']
    path_ext = config['path_ext']
    try:
        package_can = package_funcs[0](result[:-1], modelsMap, callbacks,
                                       config.get('release'))
        package_can['uri'] = can_url.format(bucket, max_date, name)
        package_ext = package_funcs[1](result[:-1], update_models_map(),
                                       update_callbacks(), config.get('release'))
        package_ext['uri'] = ext_url.format(bucket, max_date, name)
    except Exception as e:
        logger.info('Error: {}'.format(e))
        return
    if nth == 1:
        pretty_package_can = package_funcs[0](result[:24], modelsMap,
                callbacks, config.get('release'))
        pretty_package_can['uri'] = can_url.format(bucket, max_date,
                'example.json')
        pretty_package_ext = package_funcs[1](result[:24], update_models_map(),
                update_callbacks(), config.get('release'))
        pretty_package_ext['uri'] = ext_url.format(bucket, max_date,
                'example.json')
        dump_json(path_can, 'example.json', pretty_package_can, pretty=True)
        dump_json(path_ext, 'example.json', pretty_package_ext, pretty=True)
    dump_json(path_can, name, package_can)
    dump_json(path_ext, name, package_ext)
    logger.info('End {}th dump startdoc={} enddoc={}'.format(nth, start, end))


def run():
    args = parse_args()
    config = read_config(args.config)
    bucket = connect_bucket(config)
    _tenders = TendersStorage(config['tenders_db']['url'],
                                  config['tenders_db']['name'])
    logger.info('Start packaging')
    nam = 'records' if args.rec else 'releases'
    if args.dates:
        datestart, datefinish = parse_dates(args.dates)
        to_release = _tenders.get_between_dates(datestart, datefinish)
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
        max_date = _tenders.get_max_date().split('T')[0]
        total = int(args.number) if args.number else 4096
        key_ids = fetch_ids(_tenders, total)
        logger.info('Fetched key doc ids')
        pool = mp.Pool(mp.cpu_count())
        _conn = partial(fetch_and_dump,
                        config,
                        max_date,
                        record=args.rec,
                        contracting=args.contracting)
        params = enumerate(
            zip_longest(key_ids, key_ids[1::], fillvalue=''),
            1
        )
        pool.map(_conn, params)
        paths = [config.get('path_can'), config.get('path_ext')]
        pool = mp.Pool(2)
        create_zip = partial(make_zip, '{}.zip'.format(nam))
        pool.map(create_zip, paths)
        create_htm = partial(create_html, ENV, config, max_date)
        pool.map(create_htm, paths)
        if args.s3 and bucket:
            put_s3 = partial(put_to_s3, bucket, max_date)
            pool.map(put_s3, paths)
            update_index(ENV, bucket)
