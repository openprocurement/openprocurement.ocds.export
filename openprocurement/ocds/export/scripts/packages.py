# -*- coding: utf-8 -*-
import argparse
import yaml
import iso8601
import os
import logging
import shutil
import math
import zipfile
from logging.config import dictConfig
from simplejson import dump, load
from jinja2 import Environment, PackageLoader
from openprocurement.ocds.export.helpers import mode_test
from openprocurement.ocds.export.storage import TendersStorage
from openprocurement.ocds.export.models import package_tenders
from uuid import uuid4
from boto.s3 import connect_to_region
from boto.s3.connection import OrdinaryCallingFormat, S3ResponseError
from filechunkio import FileChunkIO


URI = 'https://fake-url/tenders-{}'.format(uuid4().hex)
Logger = logging.getLogger(__name__)
ENV =  Environment(loader=PackageLoader('openprocurement.ocds.export', 'templates'))
try:
    CONN = connect_to_region(
                'eu-west-1',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', ''),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
                calling_format=OrdinaryCallingFormat()
                )
    BUCKET = CONN.get_bucket('ocds.prozorro.openprocurement.io')
except S3ResponseError as e:
    Logger.warn('Unable to connect to s3. Error: {}'.format(e))


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
    parser.add_argument('-s3', action='store_true', help="Choose to start uploading to aws s3", default=False)
    parser.add_argument('-p', '--pretty', action='store_true', default=False, help='Create pretty printed release')
    return parser.parse_args()


def parse_dates(dates):
    return iso8601.parse_date(dates[0]).isoformat(), iso8601.parse_date(dates[1]).isoformat()


def make_zip(name, base_dir, skip=[]):
    skip.append(name)
    with zipfile.ZipFile(os.path.join(base_dir, name), 'w', allowZip64=True) as zf:
        for f in [f for f in os.listdir(base_dir) if f not in skip]:
            zf.write(os.path.join(base_dir, f))



def dump_package(tenders, config, pack_num=None, pprint=None):
    try:
        package = package_tenders(tenders, config.get('release'))
        date = max(map(lambda x: x.get('date', ''), package['releases']))

    except Exception as e:
        Logger.info('Error: {}'.format(e))
        return
    if pprint:
        path = os.path.join(config['path'], 'example.json')
        with open(path, 'w') as outfile:
            dump(package, outfile, indent=4)
    else:
        path = os.path.join(config['path'], 'release-{0:07d}.json'.format(pack_num))
        with open(path, 'w') as outfile:
            dump(package, outfile)
    return date


def put_to_s3(path, time):
    dir_name = 'merged_{}'.format(time)
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


def file_size(path, name):
    return (os.stat(os.path.join(path, name)).st_size) / 1000000

def get_torrent_link(bucket, path):
    return 'https://s3-eu-west-1.amazonaws.com/{}/{}/releases.zip?torrent'.format(bucket, path)

def create_html(path, config, date):
    template = ENV.get_template('index.html')
    links = []
    for file in [f for f in os.listdir(path) if
                 f not in ['example.json', 'index.html', 'releases.zip']]:
        link = {}
        link['size'] = file_size(path, file) 
        link['link'] = file
        links.append(link)
    torrent_link = get_torrent_link(config.get('bucket'), 'merged_{}'.format(date))
    zip_size = file_size(path, 'releases.zip')
    with open(os.path.join(path, 'index.html'), 'w') as stream:
        stream.write(template.render(dict(zip_size=zip_size, torrent_link=torrent_link, links=links)))


def update_index(time):
    key = BUCKET.new_key('index.html')
    key.get_contents_to_filename('index.html')
    dir_name = 'merged_{}'.format(time)
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
    max_date = None
    if not os.path.exists(config.get('path')):
        os.makedirs(config.get('path'))
    if args.dates:
        datestart, datefinish = parse_dates(args.dates)
        tenders = [t['value'] for t in _tenders.db.view('tenders/byDateModified',
                                                        startkey=datestart,
                                                        endkey=datefinish)]
        max_date = dump_package(tenders, config)
    else:
        count = 0
        total = int(args.number) if args.number else 4096
        tenders = []
        gen_pprinted = True
        for tender in _tenders:
            tenders.append(tender)
            count += 1
            if count == 24 and gen_pprinted:
                date = dump_package(tenders, config, pprint=True)
                if max_date is None or max_date < date:
                    max_date = date

                Logger.info('dumping pprint {} packages'.format(len(tenders)))
                gen_pprinted = False
            if count == total:
                Logger.info('dumping {} packages'.format(len(tenders)))
                date = dump_package(tenders, config, pack_num)
                if max_date is None or max_date < date:
                    max_date = date
                pack_num += 1
                count = 0
                tenders = []
    date = max_date.split('T')[0]
    Logger.fatal(date)
    make_zip('releases.zip', config.get('path'))
    create_html(config.get('path'), config, date)
    if args.s3:
        put_to_s3(config.get('path'), date)
    update_index(date)
