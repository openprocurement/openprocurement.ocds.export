import sys
from couchdb.design import ViewDefinition


class CouchView(ViewDefinition):

    def __init__(self):

        module = sys.modules[self.__module__]
        design_name = module.__name__.split('.')[-1]

        map_fun = self.__class__.map

        if hasattr(self.__class__, "reduce"):
            reduce_fun = self.__class__.reduce
        else:
            reduce_fun = None

        super(CouchView, self).__init__(
            design_name, self.__class__.design, map_fun, reduce_fun, 'python')


def get_db_url(user, password, host, port, name=''):
    prefix = ''
    if user:
        prefix = "{}:{}@".format(user, password)
    return "http://{}{}:{}/".format(
        prefix,
        host,
        port,
        name
    )
