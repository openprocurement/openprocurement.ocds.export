# -*- coding: utf-8 -*-
import argparse
import yaml
import iso8601
import os
import time
import logging
import shutil
import math
from logging.config import dictConfig
from simplejson import dump
from openprocurement.ocds.export.helpers import mode_test
from openprocurement.ocds.export.storage import TendersStorage
from openprocurement.ocds.export.models import package_tenders
from uuid import uuid4
from boto.s3 import connect_to_region
from boto.s3.connection import OrdinaryCallingFormat
from filechunkio import FileChunkIO


URI = 'https://fake-url/tenders-{}'.format(uuid4().hex)
Logger = logging.getLogger(__name__)
CONN = connect_to_region(
            'eu-west-1',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            calling_format=OrdinaryCallingFormat()
            )
BUCKET = CONN.get_bucket('ocds.prozorro.openprocurement.io')

def read_config(path):
    with open(path) as cfg:
        config = yaml.load(cfg)
    dictConfig(config.get('logging', ''))
    return config


def parse_args():
    parser = argparse.ArgumentParser('Release Packages')
    parser.add_argument('-c', '--config', required=True, help="Path to configuration file")
    parser.add_argument('-d', action='append', dest='dates', default=[], help='Start-end dates to generate package')
    parser.add_argument('-n', '--number')
    parser.add_argument('-s3', action='store_true', help="Choose to start uploading to aws s3")
    return parser.parse_args()


def parse_dates(dates):
    return iso8601.parse_date(dates[0]).isoformat(), iso8601.parse_date(dates[1]).isoformat()


def dump_package(tenders, config, pack_num=None, pprint=None):
    try:
        package = package_tenders(tenders, config.get('release'))
    except Exception as e:
        Logger.info('Error: {}'.format(e))
        return
    if pprint:
        path = os.path.join(config['path'], 'pretty_printed_release.json')
        with open(path, 'w') as outfile:
            dump(package, outfile, indent=4)
    else:
        path = os.path.join(config['path'], 'release-000000{}.json'.format(pack_num))
        with open(path, 'w') as outfile:
            dump(package, outfile)


def put_to_s3(path):
    dir_name = 'merged_{}'.format(time.strftime('%d-%m-%Y'))
    for file in os.listdir(path):
        aws_path = os.path.join(dir_name, file)
        file_path = os.path.join(path, file)
        if file.split('.')[1] == 'zip':
            mp = BUCKET.initiate_multipart_upload(aws_path)
            source_size = os.stat(file_path).st_size
            chunk_size = 52428800
            chunk_count = int(math.ceil(source_size / chunk_size))
            for i in range(chunk_count + 1):
                offset = chunk_size * i
                bytes = min(chunk_size, source_size - offset)
                with FileChunkIO(file_path, 'r', offset=offset,
                                 bytes=bytes) as fp:
                    mp.upload_part_from_file(fp, part_num=i + 1)
            mp.complete_upload()
        else:
            key = BUCKET.new_key(aws_path)
            key.set_contents_from_filename(file_path)


def create_html(path):
    with open(path + '/' + 'index.html', 'w') as stream:
        stream.write("<html>\n<head></head>\n<body>\n<ol>\n")
        for file in os.listdir(path):
            link = "<li><a href='{}'>{}</a></li>\n".format(file, file)
            stream.write(link)
        stream.write("</ol></body>\n</html>")


def update_index():
    key = BUCKET.new_key('index.html')
    key.get_contents_to_filename('index.html')
    dir_name = 'merged_{}'.format(time.strftime('%d-%m-%Y'))
    with open('index.html', 'r+') as f:
        lines = f.readlines()
    lines.insert(lines.index('</ol></body>\n'), "<li><a href='{}'>{}</a></li>\n".format(dir_name, dir_name))
    with open('index.html', 'w') as f:
        f.write(''.join(lines))
    key.set_contents_from_filename('index.html')


def run():
    args = parse_args()
    config = read_config(args.config)
    pack_num = 1
    _tenders = TendersStorage(config['tenders_db']['url'], config['tenders_db']['name'])
    Logger.info('Start packaging')
    if not os.path.exists(config.get('path')):
        os.makedirs(config.get('path'))
    if args.dates:
        datestart, datefinish = parse_dates(args.dates)
        tenders = [t['value'] for t in _tenders.db.view('tenders/byDateModified', startkey=datestart, endkey=datefinish)]
        dump_package(tenders, config)
    else:
        count = 0
        total = int(args.number) if args.number else 2048
        tenders = []
        gen_pprinted = True
        for tender in _tenders:
            tenders.append(tender)
            count += 1
            if count == 24 and gen_pprinted:
                dump_package(tenders, config, pprint=True)
                Logger.info('dumping pprint {} packages'.format(len(tenders)))
                gen_pprinted = False
            if count == total:
                Logger.info('dumping {} packages'.format(len(tenders)))
                dump_package(tenders, config, pack_num)
                pack_num += 1
                count = 0
                tenders = []
        if tenders:
            Logger.info('dumping {} packages'.format(len(tenders)))
            dump_package(tenders, config)
    create_html(config.get('path'))
    shutil.make_archive('releases_archived', 'zip', 'patches')
    if args.s3:
        put_to_s3(config.get('path'))
    update_index()
