"""
Pagination classes providing more complete pagination metadata.
"""

# Mostly from djangorestframework-jsonapi

import collections

from rest_framework import pagination
from rest_framework.utils import urls
from rest_framework import response


class PageNumberPagination(pagination.PageNumberPagination):
    """
    Page number pagination with more complete metadata.
    """

    page_size_query_param = 'page_size'
    max_page_size = 100

    def build_link(self, index):
        if not index:
            return None
        url = self.request and self.request.build_absolute_uri() or ''
        return urls.replace_query_param(url, self.page_query_param, index)

    def get_paginated_response(self, data):
        next = None
        previous = None

        if self.page.has_next():
            next = self.page.next_page_number()
        if self.page.has_previous():
            previous = self.page.previous_page_number()

        return response.Response(collections.OrderedDict([
            ('results', data),
            ('page', self.page.number),
            ('pages', self.page.paginator.num_pages),
            ('count', self.page.paginator.count),
            ('first', self.build_link(1)),
            ('last', self.build_link(self.page.paginator.num_pages)),
            ('next', self.build_link(next)),
            ('previous', self.build_link(previous)),
        ]))


class LimitOffsetPagination(pagination.LimitOffsetPagination):
    """
    Limit/offset pagination with more complete metadata.
    """
    limit_query_param = 'page[limit]'
    offset_query_param = 'page[offset]'

    def get_last_link(self):
        if self.count == 0:
            return None

        url = self.request.build_absolute_uri()
        url = urls.replace_query_param(url, self.limit_query_param, self.limit)

        offset = (self.count // self.limit) * self.limit

        return urls.replace_query_param(url, self.offset_query_param, offset)

    def get_first_link(self):
        if self.count == 0:
            return None

        url = self.request.build_absolute_uri()
        return urls.remove_query_param(url, self.offset_query_param)

    def get_paginated_response(self, data):
        return response.Response(collections.OrderedDict([
            ('results', data),
            ('count', self.count),
            ('limit', self.limit),
            ('offset', self.offset),
            ('first', self.get_first_link()),
            ('last', self.get_last_link()),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
        ]))
