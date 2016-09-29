import gevent
import random
from gevent.queue import Full
from ocds.databridge.exceptions import LBMismatchError


class RetreiverForward(gevent.Greenlet):

    def __init__(self, client, params, cookie, queue, filter_func, logger):
        super(RetreiverForward, self).__init__()
        self.name = 'Forward'
        self.client = client
        self.params = params
        self.cookie = cookie
        self.queue = queue
        self.empty_response_delay = 5
        self.full_queue_delay = 3
        self.delay = 2
        self.flt = filter_func
        self.logger = logger

    def _run(self):
        self.logger.info("{} starting".format(self.name))
        while True:
            try:
                r = self.client.get_tenders(self.params)

                if self.client.session.cookies != self.cookie:
                    self.logger.error("{} lb mismatch error, exit".format(self.name))
                    raise LBMismatchError

                if r['data']:
                    self.logger.info("{} got response {} items".format(self.name, len(r['data'])))
                    try:
                        self.queue.put(filter(self.flt, r['data']))
                    except Full:
                        self.logger.warn('{} queue is full, waiting'.format(self.name))
                        while self.queue.full():
                            gevent.sleep(self.full_queue_delay)
                        self.queue.put(filter(self.flt, r['data']))

                    gevent.sleep(random.uniform(0, 2) * self.delay)

                else:
                    self.logger.warn('{} got empty response..sleeping'.format(self.name))
                    gevent.sleep(random.uniform(0, 2) *
                                 self.empty_response_delay)

                self.params['offset'] = r['next_page']['offset']

            except LBMismatchError:
                raise gevent.GreenletExit
            except Exception as e:
                self.logger.error("{} failed on {}".format(self.name, e))
                return 0
        return 1
        self.logger.warn('{} finished'.format(self.name))


class RetreiverBackward(gevent.Greenlet):


    def __init__(self, client, params, cookie, queue, filter_func, logger):
        super(RetreiverBackward, self).__init__()
        self.name = 'Backward'
        self.client = client
        self.params = params
        self.cookie = cookie
        self.queue = queue
        self.full_queue_delay = 3
        self.delay = 0.7
        self.logger = logger
        self.flt = filter_func

    def _run(self):
        self.logger.info("{} starting".format(self.name))
        r = self.client.get_tenders(self.params)
        if self.client.session.cookies != self.cookie:
            self.logger.error("{} lb mismatch error, exit".format(self.name))
            raise LBMismatchError
        if r['data']:
            self.queue.put(filter(self.flt, r['data']))
        while r['data']:
            self.logger.info("{} got response {} items".format(self.name, len(r['data'])))
            try:
                r = self.client.get_tenders(self.params)

                if self.client.session.cookies != self.cookie:
                    self.logger.error("{} lb mismatch error, exit".format(self.name))
                    raise LBMismatchError

                try:
                    self.queue.put(filter(self.flt, r['data']))
                except Full:
                    self.logger.warn('{} queue is full, waiting'.format(self.name))
                    while self.queue.full():
                        gevent.sleep(self.full_queue_delay)
                self.queue.put(filter(self.flt, r['data']))

                gevent.sleep(random.uniform(0, 2) * self.delay)

                self.params['offset'] = r['next_page']['offset']

            except LBMismatchError:
                raise gevent.GreenletExit

        self.logger.warn('{} finished'.format(self.name))
        return 1
