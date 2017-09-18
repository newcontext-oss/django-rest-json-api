"""
Test the basic DRF-formatted STIX type-specific endpoints.
"""

from django_rest_json_api import tests


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
        self.assertHAR(self.example)

    def test_json_api_error_example(self):
        """
        Test the jsonapi.org error response example.
        """
        self.setUpHAR('error.api+json.har.json')
        self.assertHAR(self.example)

    def test_json_api_pagination_example(self):
        """
        Test the jsonapi.org pagination example.
        """
        self.setUpHAR('pagination.api+json.har.json')
        self.skipTest('TODO Implement pagination')
        # self.assertHAR(self.example)

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
