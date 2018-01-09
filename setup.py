from setuptools import setup, find_packages


DESCRIPTION = """
    Libraty for generating packages
    in OCDS release format from openprocurement data
"""
install_requires = [
    'setuptools',
    'iso8601',
    'simplejson',
    'ocdsmerge==0.3',
    'jsonpatch',
    'CouchDB',
    'python-dateutil',
    'requests',
    'gevent',
    'PyYaml',
    'boto3',
    'boto',
    'Jinja2',
    'google-compute-engine'
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

setup(name='openprocurement_ocds_export',
      version='0.1.0+py3',
      description=DESCRIPTION,
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      include_package_data=True,
      packages=find_packages(exclude=['ez_setup']),
      zip_safe=False,
      install_requires=install_requires,
      tests_require=test_requires,
      entry_points=entry_points
      )
