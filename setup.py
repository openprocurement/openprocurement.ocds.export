from setuptools import setup

DESCRIPTION = """
    Libraty for generating packages
    in OCDS release format from openprocurement data
"""
VERSION = "1.0.1a1+bridge"


install_requires = [
    'setuptools',
    'iso8601',
    'simplejson',
    'jsonpatch',
    'CouchDB',
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
      version=VERSION,
      description=DESCRIPTION,
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      include_package_data=True,
      packages=['openprocurement.ocds.export'],
      zip_safe=False,
      install_requires=install_requires,
      tests_require=test_requires,
      entry_points=entry_points
      )
