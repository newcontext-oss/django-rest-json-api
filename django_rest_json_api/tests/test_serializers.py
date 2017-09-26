import json

import pkg_resources

from rest_framework.settings import api_settings
from rest_framework import exceptions
from rest_framework import request
from rest_framework import pagination
from rest_framework import test

from django_rest_json_api import serializers
from django_rest_json_api import renderers
from django_rest_json_api import tests

from django_rest_json_api_example import models
from django_rest_json_api_example import serializers as example_serializers
from django_rest_json_api_example import views


class DRFJSONAPISerializerTests(tests.JSONAPITestCase):

    def test_resource_internal_value(self):
        """
        The resource serializer desserializes JSON API resource identity.
        """
        resource_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"][0],
            field_inflectors=serializers.field_inflectors)
        resource_serializer.is_valid(raise_exception=True)
        article_serializer = example_serializers.ArticleSerializer(
            data=example_serializers.ArticleSerializer(
                instance=self.article).data)
        article_serializer.is_valid(raise_exception=True)
        self.assertEqual(
            # Cast to normal dicts for more informative failures
            dict(resource_serializer.validated_data),
            dict(article_serializer.validated_data),
            'Wrong deserialized internal value')
        saved = resource_serializer.save()
        self.assertIsInstance(
            saved, models.Article,
            'Wrong saved resource type')

    def test_resource_internal_value_many(self):
        """
        The resource serializer desserializes multiple resources.
        """
        resource_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"],
            context=dict(request=self.articles_request))
        resource_serializer.is_valid(raise_exception=True)
        self.assertIsInstance(
            resource_serializer.validated_data, list,
            'Wrong deserialized multiple value type')
        internal_value = resource_serializer.to_internal_value(
            self.content["data"])
        self.assertIsInstance(
            internal_value, list,
            'Wrong deserialized multiple value type')
        validated_value = resource_serializer.validate(internal_value)
        self.assertIsInstance(
            validated_value, list,
            'Wrong deserialized multiple value type')
        article_serializer = example_serializers.ArticleSerializer(
            data=example_serializers.ArticleSerializer(
                instance=[self.article], many=True).data, many=True)
        article_serializer.is_valid(raise_exception=True)
        self.assertEqual(
            # Cast to normal dicts for more informative failures
            dict(resource_serializer.validated_data[0]),
            dict(article_serializer.validated_data[0]),
            'Wrong deserialized internal value')
        self.assertEqual(
            # Cast to normal dicts for more informative failures
            dict(internal_value[0]),
            dict(article_serializer.validated_data[0]),
            'Wrong deserialized internal value')
        self.assertEqual(
            # Cast to normal dicts for more informative failures
            dict(validated_value[0]),
            dict(article_serializer.validated_data[0]),
            'Wrong deserialized internal value')
        saved = resource_serializer.save()
        self.assertIsInstance(
            resource_serializer.data, list,
            'Wrong saved representation multiple value type')
        self.assertIsInstance(
            saved, list,
            'Wrong saved instance type')
        self.assertIsInstance(
            saved[0], models.Article,
            'Wrong saved instance type')
        with self.assertRaises(NotImplementedError):
            resource_serializer.save()
        updated = resource_serializer.update(
            saved[0], resource_serializer.validated_data[0])
        self.assertIsInstance(
            updated, models.Article,
            'Wrong updated instance type')

    def test_resource_representation(self):
        """
        The resource serializer sserializes JSON API resource identity.
        """
        resource_serializer = serializers.JSONAPIResourceSerializer(
            instance=self.article,
            context=dict(request=self.article_request))
        self.assertEqual(
            json.loads(json.dumps(resource_serializer.data)),
            self.content["data"][0],
            'Wrong serialized representation')

    def test_resource_representation_skipped_fields(self):
        """
        The resource serializer handles skipped fields.
        """
        resource_serializer = serializers.JSONAPIResourceSerializer(
            instance=models.Article.objects.create(title=self.article.title),
            context=dict(request=self.article_request))
        self.assertNotIn(
            'description',
            resource_serializer.data['attributes'],
            'Skipped field in serialized representation')
        self.assertNotIn(
            'author',
            resource_serializer.data['relationships'],
            'Skipped field in serialized representation')

    def test_link_as_url_string(self):
        """
        The link serializer accepts an argument to use URL strings.
        """
        link_serializer = serializers.JSONAPILinkSerializer(
            instance={'href': self.article},
            context=dict(request=self.article_request),
            as_url_string=True)
        representation = link_serializer.to_representation(
            link_serializer.instance)
        self.assertEqual(
            representation,
            self.content["data"][0]["links"]["self"],
            'Wrong link representation')
        value = link_serializer.to_internal_value(representation)
        self.assertEqual(
            value, self.article,
            'Wrong link internal value')

    def test_document_internal_value(self):
        """
        The document serializer desserializes JSON API document identity.
        """
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        document_serializer.is_valid(raise_exception=True)
        self.assertIsInstance(
            document_serializer.validated_data, list,
            'Wrong internal value type')
        article_serializer = example_serializers.ArticleSerializer(
            data=example_serializers.ArticleSerializer(
                instance=[self.article], many=True).data, many=True)
        article_serializer.is_valid(raise_exception=True)
        self.assertEqual(
            document_serializer.validated_data,
            article_serializer.validated_data,
            'Wrong deserialized internal value')

    def test_document_internal_value_single(self):
        """
        The document serializer desserializes JSON API document identity.
        """
        self.content["data"] = self.content["data"][0]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        document_serializer.is_valid(raise_exception=True)
        self.assertIsInstance(
            document_serializer.validated_data, dict,
            'Wrong internal value type')
        article_serializer = example_serializers.ArticleSerializer(
            data=example_serializers.ArticleSerializer(
                instance=self.article).data)
        article_serializer.is_valid(raise_exception=True)
        self.assertEqual(
            document_serializer.validated_data,
            article_serializer.validated_data,
            'Wrong deserialized internal value')
        updated = document_serializer.update(
            self.article, document_serializer.validated_data)
        self.assertIsInstance(
            updated, models.Article,
            'Wrong updated type')
        created = document_serializer.create(
            document_serializer.validated_data)
        self.assertIsInstance(
            created, models.Article,
            'Wrong created type')
        saved = document_serializer.save()
        self.assertIsInstance(
            saved, models.Article,
            'Wrong saved type')

    def test_document_representation(self):
        """
        The document serializer sserializes JSON API document identity.
        """
        # Ignore pagination when using serializers directly
        del self.content["links"]["first"]
        del self.content["links"]["last"]
        del self.content["links"]["prev"]
        del self.content["links"]["next"]
        del self.content["meta"]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            instance=[self.article],
            context=dict(request=self.articles_request))
        # Normalize OrderedDicts to dicts for assertions
        data = json.loads(json.dumps(document_serializer.data))
        self.assertEqual(
            data, self.content,
            'Wrong serialized representation')

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

    def test_single_resource_validation(self):
        """
        The resource serializer handles single resource validation errors.
        """
        del self.content["data"][0]["attributes"]["title"]
        single_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"][0])
        with self.assertRaises(exceptions.ValidationError) as cm:
            single_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'attributes', cm.exception.detail,
            'Missing resource field attributes validation')
        self.assertIn(
            'title', cm.exception.detail['attributes'],
            'Missing required field validation')
        self.assertIn(
            'required', cm.exception.detail['attributes']['title'][0],
            'Wrong required field validation error')

    def test_multiple_resource_validation(self):
        """
        The resource serializer handles multiple resources validation errors.
        """
        del self.content["data"][0]["attributes"]["title"]
        multi_serializer = serializers.JSONAPIResourceSerializer(
            data=self.content["data"])
        with self.assertRaises(exceptions.ValidationError) as cm:
            multi_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'attributes', cm.exception.detail[0],
            'Missing resource field attributes validation')
        self.assertIn(
            'title', cm.exception.detail[0]['attributes'],
            'Missing required field validation')
        self.assertIn(
            'required', cm.exception.detail[0]['attributes']['title'][0],
            'Wrong required field validation error')
        self.assertIn(
            'attributes', multi_serializer.errors[0],
            'Missing resource field attributes validation')
        self.assertIn(
            'title', multi_serializer.errors[0]['attributes'],
            'Missing required field validation')
        self.assertIn(
            'required', multi_serializer.errors[0]['attributes']['title'][0],
            'Wrong required field validation error')

    def test_field_reserved_conflict_validation(self):
        """
        The document serializer validates reserved field names and conflicts.
        """
        self.content["data"][0]["attributes"][
            "type"] = self.content["data"][0]["type"]
        self.content["data"][0]["relationships"][
            "type"] = self.content["data"][0]["relationships"]["author"]
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
        self.author_jsonapi["attributes"][
            "type"] = self.content["data"][0]["type"]
        resource_serializer = serializers.JSONAPIResourceSerializer(
            data=self.author_jsonapi)
        with self.assertRaises(exceptions.ValidationError) as cm:
            resource_serializer.is_valid(raise_exception=True)
        self.assertIn(
            "a resource can not have 'attributes' fields named",
            cm.exception.detail["attributes"][0].lower(),
            'Wrong reserved field name validation error')

    def test_relationships_type_validation(self):
        """
        The document serializer validates the relationships object type.
        """
        self.content["data"][0]["relationships"] = [
            self.content["data"][0]["relationships"]]
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'expected a dictionary',
            cm.exception.detail["data"][0]['relationships'][0].lower(),
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
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'must contain at least one',
            cm.exception.detail["data"][0]['relationships'][0].lower(),
            'Wrong relationships object missing must validation error')

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
            instance=[self.article, self.article],
            context=dict(request=self.articles_request))
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.data
        self.assertIn(
            'must not include more than one resource',
            cm.exception.detail["/data/articles/{0}".format(
                self.article.uuid)][0].lower(),
            'Wrong `errors` with `data` validation error')
        self.skipTest('TODO add coverage when we implement included')

    def test_version_internal_value(self):
        """
        The JSON API version is parsed.
        """
        version_serializer = serializers.JSONAPIImplementationSerializer(
            data=self.content["jsonapi"])
        version_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'version', version_serializer.validated_data,
            'Missing JSON API version')
        self.assertIsInstance(
            version_serializer.validated_data['version'],
            pkg_resources.SetuptoolsVersion,
            'Wrong JSON API parsed version type')

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

    def test_included_internal_value_validation(self):
        """
        Included resources on POST are undefined.
        """
        self.content['included'] = self.included
        document_serializer = serializers.JSONAPIDocumentSerializer(
            data=self.content)
        with self.assertRaises(exceptions.ValidationError) as cm:
            document_serializer.is_valid(raise_exception=True)
        self.assertIn(
            'may not contain `included`',
            cm.exception.detail['included'][0].lower(),
            'Wrong `errors` with `data` validation error')

    def test_flatten_error_details_nested_list(self):
        """
        Test recursively flattening error details.
        """
        detail = [[exceptions.ErrorDetail('Foo error detail')]]
        flattened = list(serializers.flatten_error_details(detail))
        self.assertEqual(
            len(flattened), 1,
            'Wrong number of flattened error details')
        self.assertEqual(
            len(flattened[0]), 2,
            'Wrong flattened error detail item type')
        self.assertEqual(
            flattened[0][0], '/0',
            'Wrong flattened error detail source pointer')
        self.assertEqual(
            flattened[0][1], str(detail[0][0]),
            'Wrong flattened error detail message')

    def test_drf_default_pagination(self):
        """
        Test the JSON API handling of the DRF default pagination.
        """
        view = views.ArticlesViewSet()
        factory = test.APIRequestFactory()
        view.request = request.Request(factory.get('/articles/'))
        view.format_kwarg = None
        view.request.accepted_renderer = renderers.JSONAPIRenderer()
        view.pagination_class = pagination.PageNumberPagination
        view.request.accepted_renderer.pagination_serializer_class = (
            serializers.JSONAPIPaginationSerializer)
        response = view.list(view.request)
        self.assertIn(
            'links', response.data,
            'Response missing top-level links')
        self.assertIn(
            'next', response.data['links'],
            'Response missing pagination link')
        self.assertIsNone(
            response.data['links']['next'],
            'Wrong pagination empty link value')
