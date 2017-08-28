from setuptools import setup
from setuptools.extension import Extension

try:
    from Cython.Build import cythonize
    cython = True
except ImportError:
    cython = False


DESCRIPTION = """
    Libraty for generating packages
    in OCDS release format from openprocurement data
"""


if cython:
    ext = cythonize(Extension(
        'openprocurement.ocds.export.models',
        ['openprocurement/ocds/export/models.pyx']),
        Extension(
        'openprocurement.ocds.export.ext.models',
        ['openprocurement/ocds/export/ext/models.pyx'])
    )

else:
    ext = [Extension(
        'openprocurement.ocds.export.models',
        ['openprocurement/ocds/export/models.c']),
        Extension(
        'openprocurement.ocds.export.ext.models',
        ['openprocurement/ocds/export/ext/models.c']),
    ]

install_requires = [
    'setuptools',
    'iso8601',
    'simplejson',
    'ocdsmerge',
    'jsonpatch',
    'CouchDB',
    'python-dateutil',
    'requests',
    'gevent',
    'PyYaml',
    'boto3',
    'boto',
    'Jinja2',
]

test_requires = [
    'pytest',
    'pytest-cov'
]


entry_points = {
    'console_scripts': [
        'bridge = openprocurement.ocds.export.scripts.run:run',
        'packages = openprocurement.ocds.export.scripts.packages:run',
        'releases = openprocurement.ocds.export.scripts.release:run'
    ]
}

setup(name='openprocurement.ocds.export',
      version='0.1.0',
      description=DESCRIPTION,
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      include_package_data=True,
      packages=['openprocurement.ocds.export'],
      zip_safe=False,
      install_requires=install_requires,
      tests_require=test_requires,
      ext_modules=ext,
      entry_points=entry_points
      )
