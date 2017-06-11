from setuptools import setup, find_packages
import sys, os

version = '0.1'

tests_require = ['django-setuptest']

setup(name='django-rest-json-api',
      version=version,
      description="JSON API implementation for Django Rest Framework",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='rest django json json-api drf',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      url='https://github.com/rpatterson/django-rest-json-api',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Django',
      ],
      test_suite='setuptest.setuptest.SetupTestSuite',
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
