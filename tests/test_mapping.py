from ocds.export.base import Mapping


def test_map_create():
    mapp = Mapping({'a': 1, 'b': 2})

    assert hasattr(mapp, 'a')
    assert hasattr(mapp, 'b')
    assert mapp.a == 1
    assert mapp.b == 2
    assert len(mapp) == 2


def test_map_nested():
    mapp = Mapping({
        'a': 1,
        'b': {
            'c': 2,
        },
        'd': {
            'e': {
                'f': 4,
            },
        },
        'g': [{
            'h': 1,
            'i': [{'j': 3}]
        }]
    })

    assert hasattr(mapp, 'a')
    assert hasattr(mapp, 'b')
    assert isinstance(mapp.b, Mapping)
    assert hasattr(mapp.b, 'c')
    assert mapp.b.c == 2
    assert hasattr(mapp.d, 'e')
    assert isinstance(mapp.d.e, Mapping)
    assert hasattr(mapp.d.e, 'f')

    assert mapp.d.e.f == 4

    assert hasattr(mapp, 'g')
    assert isinstance(mapp.g, list)
    assert isinstance(mapp.g[0], Mapping)
    assert mapp.g[0].h == 1
    assert isinstance(mapp.g[0].i, list)
    assert isinstance(mapp.g[0].i[0], Mapping)
    assert mapp.g[0].i[0].j == 3
    assert len(mapp) == 4


def test_change():
    mapp = Mapping({'a': 1, 'b': 2})
    assert mapp.a == 1

    mapp.a = 2
    assert mapp.a == 2
    mapp = Mapping({'a': 1, 'c': {'b': 2}})
    assert mapp.c.b == 2
    mapp.c.b = 3
    assert mapp.c.b == 3


def test_set_get():
    mapp = Mapping({'a': 1, 'b': 2})
    mapp['a'] = 2
    assert mapp.a == 2
    assert mapp['a'] == 2

    mapp['b'] = ['a']
    assert isinstance(mapp['b'], list)
    assert isinstance(mapp.b, list)
    assert mapp['b'] == ['a']

    mapp['c'] = {'a': 1}
    assert isinstance(mapp.c, Mapping)
    assert hasattr(mapp.c, 'a')
    assert mapp.c.a == 1

    mapp['d'] = [{'a': 1}]
    assert isinstance(mapp.d[0], Mapping)
    assert mapp.d[0].a == 1


def test_del():
    mapp = Mapping({'a': 1, 'c': {'b': 2}})
    del mapp.a
    assert not hasattr(mapp, 'a')
    del mapp.c.b
    assert hasattr(mapp, 'c')
    assert not hasattr(mapp.c, 'b')


def test_iter():
    mapp = Mapping({'a': 1, 'c': {'b': 2}})
    assert ['a', 'c'] == mapp.keys()

    assert [1, {'b': 2}] == mapp.values()

    assert [('a', 1), ('c', {'b': 2})] == mapp.items()


def test_unwrap():
    data = {'a': 1, 'c': {'b': 2}, 'd': [{'a': [1, 2, 3]}]}
    mapp = Mapping(data)
    assert data == mapp.unwrap()
