from setuptools import setup, find_packages
import os

version = '0.1'

tests_require = ['test-har', 'django-setuptest']

setup(name='django-rest-json-api',
      version=version,
      description="JSON API implementation for Django Rest Framework",
      long_description=open(os.path.join(
          os.path.dirname(__file__), 'README.rst')).read(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Internet',
          'Topic :: Internet :: WWW/HTTP',
      ],
      keywords='rest django json json-api drf',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      url='https://github.com/rpatterson/django-rest-json-api',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      setup_requires=['setuptools-git'],
      install_requires=[
          'Django', 'djangorestframework',
      ],
      test_suite='setuptest.setuptest.SetupTestSuite',
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
