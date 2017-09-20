"""
Test our more complete pagination classes.
"""

# Mostly from djangorestframework-jsonapi

from collections import OrderedDict

from rest_framework import request
from rest_framework import test
from rest_framework.utils import urls

from django_rest_json_api.pagination import LimitOffsetPagination

factory = test.APIRequestFactory()


class TestLimitOffset(test.APISimpleTestCase):
    """
    Unit tests for `pagination.LimitOffsetPagination`.
    """

    def setUp(self):
        class ExamplePagination(LimitOffsetPagination):
            default_limit = 10
            max_limit = 15

        self.pagination = ExamplePagination()
        self.queryset = range(1, 101)
        self.base_url = 'http://testserver/'

    def paginate_queryset(self, request):
        return list(self.pagination.paginate_queryset(self.queryset, request))

    def get_paginated_content(self, queryset):
        response = self.pagination.get_paginated_response(queryset)
        return response.data

    def get_request(self, arguments):
        return request.Request(factory.get('/', arguments))

    def test_valid_offset_limit(self):
        """
        Basic test, assumes offset and limit are given.
        """
        offset = 10
        limit = 5
        count = len(self.queryset)
        last_offset = (count // limit) * limit
        next_offset = 15
        prev_offset = 5

        request = self.get_request({
            self.pagination.limit_query_param: limit,
            self.pagination.offset_query_param: offset
        })
        base_url = urls.replace_query_param(
            self.base_url, self.pagination.limit_query_param, limit)
        last_url = urls.replace_query_param(
            base_url, self.pagination.offset_query_param, last_offset)
        first_url = base_url
        next_url = urls.replace_query_param(
            base_url, self.pagination.offset_query_param, next_offset)
        prev_url = urls.replace_query_param(
            base_url, self.pagination.offset_query_param, prev_offset)
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        next_offset = offset + limit

        expected_content = OrderedDict([
            ('results', list(range(offset + 1, next_offset + 1))),
            ('count', count),
            ('limit', limit),
            ('offset', offset),
            ('first', first_url),
            ('last', last_url),
            ('next', next_url),
            ('previous', prev_url),
        ])

        self.assertEqual(queryset, list(range(offset + 1, next_offset + 1)))
        self.assertDictEqual(content, expected_content)

    def test_valid_offset_zero_count(self):
        """
        Test limit/offset paging when the count is 0.
        """
        self.queryset = []

        offset = 10
        limit = 5
        count = len(self.queryset)
        prev_offset = 5

        request = self.get_request({
            self.pagination.limit_query_param: limit,
            self.pagination.offset_query_param: offset
        })
        base_url = urls.replace_query_param(
            self.base_url, self.pagination.limit_query_param, limit)
        prev_url = urls.replace_query_param(
            base_url, self.pagination.offset_query_param, prev_offset)
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)

        expected_content = OrderedDict([
            ('results', []),
            ('count', count),
            ('limit', limit),
            ('offset', offset),
            ('first', None),
            ('last', None),
            ('next', None),
            ('previous', prev_url),
        ])

        self.assertEqual(queryset, [])
        self.assertDictEqual(content, expected_content)
