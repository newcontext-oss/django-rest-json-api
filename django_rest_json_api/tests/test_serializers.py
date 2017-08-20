import json
import copy
import operator

from rest_framework import exceptions
from rest_framework.settings import api_settings

from django_rest_json_api import serializers
from django_rest_json_api import tests

from django_rest_json_api_example import models


class ExampleDictErrorSerializer(serializers.JSONAPIResourceSerializer):
    """
    Raise a single dict error for tests.
    """

    def validate(self, attrs):
        """
        Raise a single dict error for tests.
        """
        raise exceptions.ValidationError({'foo': 'foo dict error'})


class DRFJSONAPISerializerTests(tests.JSONAPITestCase):

    def test_document(self):
        """
        The document serializer handles JSON API example HAR.
        """
        self.content.pop("included", None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        document_serializer.is_valid(raise_exception=True)
        self.assertIsInstance(
            document_serializer.validated_data,
            type(self.content["data"]),
            'Wrong parsed JSON API primary data type')
        self.assertIn(
            'uuid', document_serializer.validated_data[0],
            'Missing parsed JSON API ID')
        self.assertEqual(
            str(document_serializer.validated_data[0]['uuid']),
            self.content['data'][0]['id'],
            'Wrong parsed JSON API ID value')
        self.assertIn(
            'title', document_serializer.validated_data[0],
            'Missing parsed JSON API field')
        self.assertEqual(
            document_serializer.validated_data[0]['title'],
            self.content['data'][0]['attributes']['title'],
            'Wrong parsed JSON API field value')
        self.assertIn(
            'author', document_serializer.validated_data[0],
            'Parsed JSON API missing 1-to-1 relationship')
        self.assertIsInstance(
            document_serializer.validated_data[0]['author'], models.Person,
            'Wrong parsed JSON API 1-to-1 relationship type')
        self.assertIn(
            'comments', document_serializer.validated_data[0],
            'Parsed JSON API missing 1-to-many relationship')
        self.assertIsInstance(
            document_serializer.validated_data[0]['comments'], list,
            'Wrong parsed JSON API 1-to-many relationship type')
        self.assertIsInstance(
            document_serializer.validated_data[0]['comments'][0],
            models.Comment,
            'Wrong parsed JSON API 1-to-many relationship type')

    def test_document_missing_must(self):
        """
        The document serializer returns validation errors on missing members.
        """
        self.content.pop("data", None)
        self.content.pop("errors", None)
        self.content.pop("meta", None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            api_settings.NON_FIELD_ERRORS_KEY, cm.exception.detail,
            'Missing required member validation')
        self.assertIn(
            'must contain at least one of',
            cm.exception.detail[api_settings.NON_FIELD_ERRORS_KEY][0].lower(),
            'Wrong required member validation')

    def test_multiple_resource_serializer(self):
        """
        The resource serializer handles multiple resources.
        """
        multi_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"])
        multi_serializer.is_valid(raise_exception=True)
        self.assertIsInstance(
            multi_serializer.data, type(self.content["data"]),
            'Wrong multiple resource type')
        self.assertIsInstance(
            multi_serializer.to_internal_value(self.content["data"]),
            type(self.content["data"]),
            'Wrong multiple resource type')
        self.assertIsInstance(
            multi_serializer.to_internal_value(
                self.content["data"][0]),
            type(self.content["data"][0]),
            'Wrong single resource type')
        saved = multi_serializer.save()
        self.assertIsInstance(
            saved, type(self.content["data"]),
            'Wrong saved instance type')
        self.assertIsInstance(
            saved[0], models.Article,
            'Wrong saved instance type')
        with self.assertRaises(NotImplementedError):
            multi_serializer.save()
        updated = multi_serializer.update(
            saved[0], multi_serializer.validated_data[0])
        self.assertIsInstance(
            updated, models.Article,
            'Wrong updated instance type')

    def test_single_resource_serializer(self):
        """
        The resource serializer handles single resources.
        """
        resource_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"][0])
        resource_serializer.is_valid(raise_exception=True)
        saved = resource_serializer.save()
        self.assertIsInstance(
            saved, models.Article,
            'Wrong saved instance type')
        self.assertIn(
            'id', resource_serializer.data,
            'Single resource missing field')

        validated = resource_serializer.validate(
            self.content["data"])
        self.assertIsInstance(
            validated, type(self.content["data"]),
            'Wrong multiple resource type')

    def test_multiple_resource_identifier_serializer(self):
        """
        The resource serializer handles multiple resource identifiers.
        """
        multi_identifiers = self.content["data"][0]["relationships"][
            "comments"]["data"]
        identifier_serializer = (
            serializers.JSONAPIResourceIdentifierSerializer(
                data=multi_identifiers))
        identifier_serializer.is_valid(raise_exception=True)
        self.assertIsInstance(
            identifier_serializer.validated_data,
            type(multi_identifiers),
            'Wrong multiple identifiers type')
        self.assertIsInstance(
            identifier_serializer.to_internal_value(multi_identifiers),
            type(multi_identifiers),
            'Wrong multiple identifiers type')

    def test_multiple_resource_validation(self):
        """
        The resource serializer handles multiple resources validation errors.
        """
        del self.content["data"][0]["id"]
        multi_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"])
        with self.assertRaises(exceptions.ValidationError) as cm:
            multi_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'id', cm.exception.detail[0],
            'Missing required field validation')
        self.assertIn(
            'required', cm.exception.detail[0]['id'][0],
            'Wrong required field validation error')
        self.assertIn(
            'id', multi_serializer.errors[0],
            'Missing required field validation')
        self.assertIn(
            'required', multi_serializer.errors[0]['id'][0],
            'Wrong required field validation error')

    def test_single_resource_validation(self):
        """
        The resource serializer handles single resource validation errors.
        """
        del self.content["data"][0]["id"]
        single_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"][0])
        with self.assertRaises(exceptions.ValidationError) as cm:
            single_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'id', cm.exception.detail,
            'Missing required field validation')
        self.assertIn(
            'required', cm.exception.detail['id'][0],
            'Wrong required field validation error')

    def test_link_serializer(self):
        """
        The link serializer handler both link objects and URL strings.
        """
        link_serializer = serializers.JSONAPILinkSerializer(
            instance=self.content["data"][0]["relationships"]["author"][
                "links"]["related"])
        self.assertIsInstance(
            link_serializer.data,
            type(self.content["data"][0]["relationships"]["author"][
                "links"]["related"]),
            'Wrong link object type')
        url_serializer = serializers.JSONAPILinkSerializer(
            instance=self.content["links"]["self"])
        self.assertIsInstance(
            url_serializer.to_representation(
                self.content["links"]["self"]),
            type(self.content["links"]["self"]),
            'Wrong string URL type')

    def test_single_resource(self):
        """
        The document serializer handles a single resource instead of an array.
        """
        self.content["data"] = self.content["data"][0]
        self.content.pop("included", None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        document_serializer.is_valid(raise_exception=True)

    def test_field_reserved_conflict_validation(self):
        """
        The document serializer validates reserved field names and conflicts.
        """
        self.content["data"][0]["attributes"][
            "type"] = self.content["data"][0]["type"]
        self.content["data"][0]["relationships"][
            "type"] = self.content["data"][0]["relationships"]["author"]
        self.content.pop("included", None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
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

    def test_field_reserved_conflict_empty_validation(self):
        """
        The document serializer validates field names if empty.
        """
        self.content["data"][0]["attributes"][
            "type"] = self.content["data"][0]["type"]
        del self.content["data"][0]["relationships"]
        self.content.pop("included", None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            "a resource can not have 'attributes' fields named",
            cm.exception.detail["data"][0]["attributes"][0].lower(),
            'Wrong reserved field name validation error')

    def test_relationships_type_validation(self):
        """
        The document serializer validates the relationships object type.
        """
        self.content["data"][0]["relationships"] = [
            self.content["data"][0]["relationships"]]
        self.content.pop("included", None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'expected a dictionary',
            cm.exception.detail["data"][0][0].lower(),
            'Wrong relationships object type validation error')

    def test_relationships_missing_must_validation(self):
        """
        The document serializer validates a relationship object required keys.
        """
        for relationship in self.content[
                "data"][0]["relationships"].values():
            must_members = (
                serializers.JSONAPIRelationshipSerializer.MUST_HAVE_ONE_OF)
            for member in must_members:
                relationship.pop(member, None)
        self.content.pop("included", None)
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'must contain at least one',
            cm.exception.detail["data"][0][0].lower(),
            'Wrong relationships object missing must validation error')

    def test_relationships_missing(self):
        """
        The document serializer handles missing relationships.
        """
        person = self.content["included"][0]
        del person["attributes"]
        resource_serializer = serializers.JSONAPIResourceSerializer(
            data=person)
        with self.assertRaises(exceptions.ValidationError):
            resource_serializer.is_valid(raise_exception=True)

    def test_errors_w_data_validation(self):
        """
        The document serializer validates errors with data.
        """
        self.content["errors"] = self.content["data"]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'must not coexist',
            cm.exception.detail[api_settings.NON_FIELD_ERRORS_KEY][0].lower(),
            'Wrong `errors` with `data` validation error')

    def test_duplicate_resource_validation(self):
        """
        The document serializer validates against duplicated resources.
        """
        document_serializer = serializers.JSONAPIDocumentSerializer(
            instance=[self.article, self.article])
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.data
        self.assertIn(
            'must not include more than one resource',
            cm.exception.detail["/data/articles/{0}".format(
                self.article.uuid)][0].lower(),
            'Wrong `errors` with `data` validation error')
        self.skipTest('TODO add coverage when we implement included')

    def test_errors(self):
        """
        The document serializer handles JSON API errors objects.
        """
        self.setUpHAR('error.api+json.har.json')
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        document_serializer.is_valid(raise_exception=True)
        self.assertIsInstance(
            document_serializer.validated_data,
            type(self.content["errors"]),
            'Wrong validated data JSON API errors type.')
        error = dict(
            document_serializer.validated_data[0],
            status=str(document_serializer.validated_data[0]["status"]),
            source=dict(document_serializer.validated_data[0]["source"]))
        self.assertEqual(
            error, self.content["errors"][0],
            'Validated data missing JSON API errors array.')

    def test_version_validation(self):
        """
        The JSON API version is validated.
        """
        self.content["jsonapi"]["version"] = str(
            float(self.content["jsonapi"]["version"]) + 0.1)
        version_serializer = serializers.JSONAPIImplementationSerializer(
            data=self.content["jsonapi"])
        with self.assertRaises(exceptions.ValidationError) as cm:
            version_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'version', cm.exception.detail,
            'Missing version validation error')
        self.assertIn(
            'not supported',
            cm.exception.detail['version'][0].lower(),
            'Wrong version validation error')

    def test_dict_to_representation(self):
        """
        Test rendering an dictionary to a JSON API representation.
        """
        article_jsonapi = self.content["data"][0]

        # TODO Ignore optional JSON API keys until implemented
        self.content.pop("included", None)
        self.content.pop("links", None)
        article_jsonapi.pop("links", None)
        for relationship in article_jsonapi["relationships"].values():
            relationship.pop("links", None)

        article_dict = copy.deepcopy(article_jsonapi["attributes"])
        article_dict["type"] = article_jsonapi["type"]
        article_dict["uuid"] = article_jsonapi["id"]
        article_dict["author"] = copy.deepcopy(article_jsonapi[
            "relationships"]["author"]["data"])
        article_dict["author"]["uuid"] = article_dict["author"].pop("id")
        article_dict["comments"] = copy.deepcopy(article_jsonapi[
            "relationships"]["comments"]["data"])
        for comment in article_dict["comments"]:
            comment["uuid"] = comment.pop("id")
        document_serializer = serializers.JSONAPIDocumentSerializer(
            instance=[article_dict])
        self.assertEqual(
            # Normalize OrderedDicts
            json.loads(json.dumps(document_serializer.data)),
            self.content,
            'Wrong JSON API representation content')

    def test_instance_to_representation(self):
        """
        Test rendering a django ORM instance to a JSON API representation.
        """
        self.content = self.entry["response"]["content"]["text"].copy()
        article_jsonapi = self.content["data"][0]

        # TODO Ignore optional JSON API keys until implemented
        self.content.pop("included", None)
        self.content.pop("links", None)
        article_jsonapi.pop("links", None)
        for relationship in article_jsonapi["relationships"].values():
            relationship.pop("links", None)

        document_serializer = serializers.JSONAPIDocumentSerializer(
            instance=[self.article])
        # Normalize OrderedDicts
        serializer_data = json.loads(json.dumps(document_serializer.data))
        # Make sure multiple relationships are in the same order
        serializer_data["data"][0]["relationships"][
            "comments"]["data"].sort(key=operator.itemgetter("id"))
        self.content["data"][0]["relationships"][
            "comments"]["data"].sort(key=operator.itemgetter("id"))
        self.assertEqual(
            serializer_data, self.content,
            'Wrong JSON API representation content')
