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
]

test_requires = [
    'pytest',
    'pytest-cov'
]


setup(name='ocds.export',
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
      )
