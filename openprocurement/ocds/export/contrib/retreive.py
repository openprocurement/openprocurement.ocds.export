import gevent
import random
import logging
from gevent.queue import Full
from ..exceptions import LBMismatchError


logger = logging.getLogger()


def retreiver(client, params, queue, _filter, name='forward'):
    logger.info("starting fetching feed {}".format(name))
    while True:
        r = client.get_tenders(params)
        if not r['data'] and name != 'forward':
            break
        logger.info("{} got response {} items".format(name, len(r['data'])))
        try:
            if r['data']:
                queue.put(filter(_filter, r['data']))
        except Full:
            logger.warn('{} queue is full, waiting'.format(name))
            while queue.full():
                gevent.sleep(random.uniform(0, 2))
            queue.put(filter(_filter, r['data']))
        gevent.sleep(random.uniform(0, 2) * 5)
        params['offset'] = r['next_page']['offset']
    logger.warn('{} finished'.format(name))
    return 1
