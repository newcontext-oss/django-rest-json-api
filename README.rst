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

To enable the JSON API format via DRF renderers and parsers, your views must
be DRF views that subclass
``drf_extra_fields.serializer_formats.FormatAPIView``.  The
``drf_extra_fields.serializer_formats`` module provides such subclasses which
can be imported as if from ``rest_framework.generics`` and
``rest_framework.viewsets``:

.. code:: python

    from drf_extra_fields import serializer_formats as viewsets

    from my_app import models
    from my_app import serializers


    class MyViewSet(viewsets.UUIDModelViewSet):
        """
        A viewset supporting serializer-based DRF formats.
        """
        queryset = models.MyModel.objects.all()
        serializer_class = serializers.MySerializer

Finally, the JSON API renderer and parser must be enabled in your settings and
set the default ordering parameter to match the JSON API standard:

.. code:: python

    ...
    REST_FRAMEWORK = {
    ...
        'DEFAULT_PARSER_CLASSES': (
    ...
            'django_rest_json_api.parsers.JSONAPIParser',
    ...
        ),
        'DEFAULT_RENDERER_CLASSES': (
    ...
            'django_rest_json_api.renderers.JSONAPIRenderer',
    ...
        ),
    ...
    'ORDERING_PARAM': 'sort',
    ...

You may optionally also include more pagination information using the
pagination classes in ``django_rest_json_api.pagination``.  These will affect
all formats, not just the JSON API renerer/parser:

.. code:: python

    ...
    REST_FRAMEWORK = {
    ...
    'DEFAULT_PAGINATION_CLASS':
    'django_rest_json_api.pagination.PageNumberPagination',
    ...


``django_rest_json_api`` also provides the following for re-use in other DRF
projects:

``django_rest_json_api.serializers``
  Serializers implementing the various JSON API objects.  This implementation
  currently defaults to using UUID's instead of DB pk IDs as the JSON IP
  resource ID and requires your models to have a ``uuid`` field.


-----------------------
Developing/Contributing
-----------------------

Contributions are welcome as GitHub pull requests, ``git format-patch`` patches,
etc..  Check that all tests pass on all supported environments before
contributing.

Before running tests the first time, install `tox`_.  This only needs to be
done once.  This may need to be run as root, such as with ``sudo``::

  $ pip install tox
  $ tox


----------
Motivation
----------

The existing DRF JSON API implementation `djangorestframework-jsonapi`_
requires too tight a coupling between endpoints and the format which prevents
using the same endpoints with other formats.  In particular, it requires that
your endpoint's serializers subclass `djangorestframework-jsonapi`_
serializers which change the representation output by those serializers.

This implementation seeks to be as loosely coupled as possible.  Currently it
manages to require only that your endpoint's views subclass
``drf_extra_fields.serializer_formats.FormatAPIView`` whose only change in
behavior is to use the format's ``serializer_class``, if specified on the
format, which in turn will delegate the endpoint-specific, non-format-specific
back to the view's ``serializer_class``.

The end result is that the same endpoints can be used with multiple different
formats based on content negotiation, IOW the ``Content-Type`` and ``Accept``
headers and the DRF ``format`` parameter and format suffixes.

----
TODO
----

Contributions for the following are particularly welcome:

#. Support DRF nested routers per the jsonapi.org relationship link examples
#. ``...?filter=...`` `filter parameter`_ support
#. ``...?include=...`` `included resources parameter`_ support
#. ``...?fields=...`` `sparse fieldsets parameter`_ support
#. Return ``400 Bad Request`` on `non-compliant query parameters`_
#. Support DB pk ID for the JSON API resource ``id`` as an option
#. Add coverage and support for non-model serializers
#. Figure out what to do with the code implementing the the JSON API standard
   as DRF validation that isn't appropriate for ``to_internal_value()``.
  

.. _JSON API specification: http://jsonapi.org/format/
.. _tox: https://tox.readthedocs.io/en/latest/

.. _sort parameter: http://jsonapi.org/format/#fetching-sorting
.. _filter parameter: http://jsonapi.org/format/#fetching-filtering
.. _page parameter: http://jsonapi.org/format/#fetching-pagination
.. _included resources parameter: http://jsonapi.org/format/#fetching-includes
.. _sparse fieldsets parameter: http://jsonapi.org/format/#fetching-sparse-fieldsets
.. _non-compliant query parameters: http://jsonapi.org/format/#query-parameters

.. _djangorestframework-jsonapi: http://django-rest-framework-json-api.readthedocs.io/en/stable/
