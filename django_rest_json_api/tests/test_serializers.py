import re

from test_har import django_rest_har as test_har

from django.core import validators
from django.utils import datastructures

from rest_framework import exceptions

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
        articles_jsonapi["data"][0][
            "relationships"] = datastructures.MultiValueDict({
                '.' + key: [value]
                for key, value in articles_jsonapi[
                        "data"][0]["relationships"].items()})
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi, many=True)
        document_serializer.is_valid(raise_exception=True)

        self.assertIn(
            "jsonapi", document_serializer.validated_data,
            'Validated data missing JSON API implementation object.')
        self.assertIn(
            "version", document_serializer.validated_data["jsonapi"],
            'Validated data missing JSON API version.')
        self.assertEqual(
            document_serializer.validated_data["jsonapi"]["version"],
            articles_jsonapi["jsonapi"]["version"],
            'Wrong validated data JSON API version.')

    def test_single_resource(self):
        """
        The document serializer handles a single resource instead of an array.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        articles_jsonapi["data"] = articles_jsonapi["data"][0]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi)
        document_serializer.is_valid(raise_exception=True)

    def test_field_reserved_conflict_validation(self):
        """
        The document serializer validates reserved field names and conflicts.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        articles_jsonapi["data"][0]["attributes"][
            "type"] = articles_jsonapi["data"][0]["type"]
        articles_jsonapi["data"][0]["relationships"][
            "type"] = articles_jsonapi["data"][0]["relationships"]["author"]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi, many=True)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            "a resource can not have 'relationships' fields named",
            cm.exception.detail["data"][0]["relationships"][0].lower(),
            'Wrong reserved field name validation error')
        self.assertIn(
            'a resource can not have `attributes` and `relationships` '
            'with the same name',
            cm.exception.detail["data"][0]["attributes"][0].lower(),
            'Wrong field name conflict validation error')

    def test_relationships_type_validation(self):
        """
        The document serializer validates the relationships object type.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        articles_jsonapi["data"][0]["relationships"] = [
            articles_jsonapi["data"][0]["relationships"]]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi, many=True)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'expected a dictionary',
            cm.exception.detail["data"][0]["relationships"][0].lower(),
            'Wrong relationships object type validation error')

    def test_relationships_missing_must_validation(self):
        """
        The document serializer validates a relationship object required keys.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        for relationship in articles_jsonapi[
                "data"][0]["relationships"].values():
            must_members = (
                serializers.JSONAPIRelationshipSerializer.MUST_HAVE_ONE_OF)
            for member in must_members:
                relationship.pop(member, None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi, many=True)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'must contain at least one',
            cm.exception.detail[
                "data"][0]["relationships"]["non_field_errors"][0].lower(),
            'Wrong relationships object missing must validation error')

    def test_included_wo_data_validation(self):
        """
        The document serializer validates included resources without data.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        del articles_jsonapi["data"]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'included member must not be present',
            cm.exception.detail["attributes"][0].lower(),
            'Wrong included resources without `data` validation error')

    def test_errors_w_data_validation(self):
        """
        The document serializer validates errors with data.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        articles_jsonapi["errors"] = articles_jsonapi["data"]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi, many=True)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'must not coexist',
            cm.exception.detail["attributes"][0].lower(),
            'Wrong `errors` with `data` validation error')

    def test_duplicate_resource_validation(self):
        """
        The document serializer validates against duplicated resources.
        """
        articles_jsonapi = self.entry["response"]["content"]["text"]
        articles_jsonapi["included"].append(articles_jsonapi["data"][0])
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi, many=True)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'must not include more than one resource',
            cm.exception.detail["/included/articles/1"][0].lower(),
            'Wrong `errors` with `data` validation error')

    def test_errors(self):
        """
        The document serializer handles JSON API errors objects.
        """
        self.setUpHAR('error.api+json.har.json')
        articles_jsonapi = self.entry["response"]["content"]["text"]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=articles_jsonapi)
        document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            "errors", document_serializer.validated_data,
            'Validated data missing JSON API errors array.')
