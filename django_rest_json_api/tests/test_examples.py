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
