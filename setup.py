from setuptools import setup

DESCRIPTION = """
    Databridge for generating packages
    in OCDS release format from openprocurement api
"""
install_requires = [
    'requests',
    'grequests',
    'gevent',
    'PyYaml',
    'ocds.export',
    'ocds.storage'
]

test_requires = [
]

entry_points = {
    'console_scripts': [
        'bridge = ocds.databridge.run:run'
    ]
}

setup(name='ocds.databridge',
      version='0.0.1',
      description=DESCRIPTION,
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      include_package_data=True,
      packages=['ocds.databridge'],
      zip_safe=False,
      install_requires=install_requires,
      tests_require=test_requires,
      entry_points=entry_points
      )
