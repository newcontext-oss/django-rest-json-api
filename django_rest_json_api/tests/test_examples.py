"""
Test the basic DRF-formatted STIX type-specific endpoints.
"""

import uuid

from django_rest_json_api import tests

from django_rest_json_api_example import models


class JSONAPIExamplesTest(tests.JSONAPITestCase):
    """
    Test the JSON API format parsers/renders.
    """

    maxDiff = None

    example_har = 'example.api+json.har.json'

    def test_json_api_example(self):
        """
        Test the jsonapi.org front page example.
        """
        models.Article.objects.create(author=self.author)
        self.assertHAR(self.example)

    def test_json_api_error_example(self):
        """
        Test the jsonapi.org error response example.
        """
        self.setUpHAR('error.api+json.har.json')
        self.assertHAR(self.example)

    def test_json_api_included_query_example(self):
        """
        Test the jsonapi.org included query parameter example.
        """
        self.setUpHAR('included-query.api+json.har.json')
        self.skipTest('TODO Implement included query parameters')
        # self.assertHAR(self.example)

    def test_json_api_included_fields_example(self):
        """
        Test the jsonapi.org included fields parameter example.
        """
        self.setUpHAR('included-query-fields.api+json.har.json')
        self.skipTest('TODO Implement included fields query parameters')
        # self.assertHAR(self.example)

    def test_json_api_previous_page(self):
        """
        Test paging when there's a previous page.
        """
        self.setUpHAR('prev-page.api+json.har.json')

        article_uuid = self.article.uuid
        self.article.uuid = uuid.uuid4()
        self.article.save()
        models.Article.objects.create(
            uuid=article_uuid, title=self.article.title, author=self.author)

        self.assertHAR(self.example)
