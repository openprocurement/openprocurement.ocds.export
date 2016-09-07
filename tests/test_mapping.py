from ocds.export.base import Mapping


def test_map_create():
    mapp = Mapping({'a': 1, 'b': 2})

    assert hasattr(mapp, 'a')
    assert hasattr(mapp, 'b')
    assert mapp.a == 1
    assert mapp.b == 2


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
            'h':1,
            'i': [ {'j': 3} ]
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
