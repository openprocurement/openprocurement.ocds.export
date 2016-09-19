# -*- coding: utf-8 -*-
import couchdb.client
from helpers import get_db_url, generate_id
from jsonpatch import make_patch


class CouchStorage(object):

    def __init__(self, config):
        url = get_db_url(config)
        db_config = config.get('db')
        server = couchdb.client.Server(url)
        try:
            self.db = server[db_config['net']['name']]
        except Exception as e:
            print e, "Creating new server named {}".format(db_config['net']['name'])
            self.db = server.create(db_config['net']['name'])
            pass

    def get(self, doc_id):
        try:
            doc = self.db[doc_id]
            return doc
        except Exception as e:
            print e, "Doc with such id is not in base"

    def post(self, doc, ocids, changed=False):
        if changed:
            self.db[generate_id()] = doc
        elif doc['ocid'] in ocids:
            return False
        else:
            self.db[generate_id()] = doc

    def get_releases_ocids(self):
        db = self.db
        result = db.iterview('report/ocid', 100, include_docs=True)
        return [i['value'] for i in result]

    def get_diff_and_tag(self, doc1, doc2):
        tag = []
        sample_path = ['/_rev', '/_id']
        patch = make_patch(doc1, doc2)
        for i in patch:
            if i['path'] not in sample_path:
                if i['op'] == 'replace':
                    if 'contracts' in i['path']:
                        tag.append('contractUpdate')
                    elif 'awards' in i['path']:
                        tag.append('awardUpdate')
                    elif 'tender' in i['path']:
                        tag.append('tenderUpdate')
                elif i['op'] == 'add':
                    if 'contracts' in i['path']:
                        tag.append('contract')
                    elif 'awards' in i['path']:
                        tag.append('award')
                    elif 'tender' in i['path']:
                        tag.append('tender')
        return tag

    def get_by_ocid_and_max_date(self, ocid):
        db = self.db
        dates = []
        result = db.iterview('report/ocid', 100, include_docs=True)
        dates = [i['key']['date'] for i in result if i['value'] == ocid]
        max_date = max(dates)
        result = db.iterview('report/ocid', 100, include_docs=True)
        for _res in result:
            if _res['key']['date'] == max_date and _res['value'] == ocid:
                return _res['key']
