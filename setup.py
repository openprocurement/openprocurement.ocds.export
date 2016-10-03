from setuptools import setup

DESCRIPTION = """
    Libraty which provides interfaces for storing
    OCDS release packages.
"""

install_requires = [
    'CouchDb',
    'python-dateutil'
]

test_requires = [
    'pytest',
    'pytest-cov'
]


setup(name='ocds.storage',
      version='0.0.1',
      description=DESCRIPTION,
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      include_package_data=True,
      packages=['ocds.storage'],
      zip_safe=False,
      install_requires=install_requires,
      tests_require=test_requires,
      )
