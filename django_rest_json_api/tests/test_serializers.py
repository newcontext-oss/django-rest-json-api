import re

from test_har import django_rest_har as test_har

from django.core import validators

from django_rest_json_api import serializers


class DRFJSONAPISerializerTests(test_har.HARTestCase):

    maxDiff = None

    example_har = 'example.api+json.har.json'

    def setUp(self):
        """
        Make the DRF test hostname pass URL validation.
        """
        validators.URLValidator.regex = re.compile(
            validators.URLValidator.regex.pattern.replace(
                '|localhost)', '|localhost|testserver)'))

        super(DRFJSONAPISerializerTests, self).setUp()

    def test_document(self):
        """
        The document serializer handles JSON API example HAR.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi)
        document_serializer.is_valid(raise_exception=True)
