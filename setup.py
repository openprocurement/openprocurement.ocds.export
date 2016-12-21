from setuptools import setup

DESCRIPTION = """
    Libraty for generating packages
    in OCDS release format from openprocurement data
"""


install_requires = [
    'setuptools',
    'iso8601',
    'schematics',
    'simplejson',
    'ocdsmerge',
    'jsonpatch'
    'CouchDB',
    'couchdb-schematics',
    'python-dateutil',
    'requests',
    'gevent',
    'PyYaml',
]

test_requires = [
    'pytest',
    'pytest-cov'
]


entry_points = {
    'console_scripts': [
        'bridge = openprocurement.ocds.export.scripts.run:run',
        'get_pack = openprocurement.ocds.export.scripts.packages:run',
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
      namespace_package=['openprocurement'],
      packages=['openprocurement.ocds.export'],
      zip_safe=False,
      install_requires=install_requires,
      tests_require=test_requires,
      entry_points=entry_points
      )
