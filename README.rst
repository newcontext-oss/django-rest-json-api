==============================
Django Rest Framework JSON API
==============================

An implementation of the `JSON API specification`_ for the Django REST
Framework.


------------
Installation
------------

Install as any other Python package, for example::

  $ pip install django-rest-json-api


-----
Usage
-----

`django_rest_json_api` provides the following for re-use in other DRF projects:

`django_rest_json_api.serializers`
  Serializers implementing the various JSON API objects.



-----------------------
Developing/Contributing
-----------------------

Contributions are welcome as GitHub pull requests, `git format-patch` patches,
etc..  Check that all tests pass on all supported environments before
contributing.

Before running tests the first time, install `tox`_.  This only needs to be
done once.  This may need to be run as root, such as with `sudo`::

  $ pip install tox
  $ tox


----
TODO
----

Contributions for the following are particularly welcome:

#. Test coverage on error object serializer
#. DRF format/renderer/parser supporting JSON API on any endpoint alongside
   other formats
#. `...?sort=...` `sort parameter`_ support
#. `...?filter=...` `filter parameter`_ support
#. `...?page[...]=...` `page parameter`_ support
#. `...?include=...` `included resources parameter`_ support
#. `...?fields=...` `sparse fieldsets parameter`_ support
#. Return `400 Bad Request` on `non-compliant query parameters`_
  

.. _JSON API specification: http://jsonapi.org/format/
.. _tox: https://tox.readthedocs.io/en/latest/

.. _sort parameter: http://jsonapi.org/format/#fetching-sorting
.. _filter parameter: http://jsonapi.org/format/#fetching-filtering
.. _page parameter: http://jsonapi.org/format/#fetching-pagination
.. _included resources parameter: http://jsonapi.org/format/#fetching-includes
.. _sparse fieldsets parameter: http://jsonapi.org/format/#fetching-sparse-fieldsets
.. _non-compliant query parameters: http://jsonapi.org/format/#query-parameters
