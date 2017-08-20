"""
Django REST JSON API tests.
"""

from test_har import django_rest_har as test_har

import re

from django.core import validators

from django_rest_json_api import utils
from django_rest_json_api_example import models


class JSONAPITestCase(test_har.HARTestCase):
    """
    Common JSON API test support.
    """

    longMessage = True
    maxDiff = None

    example_har = 'example.api+json.har.json'

    def setUp(self):
        """
        Make the DRF test hostname pass URL validation.
        """
        validators.URLValidator.regex = re.compile(
            validators.URLValidator.regex.pattern.replace(
                '|localhost)', '|localhost|testserver)'))

        super(JSONAPITestCase, self).setUp()

        article_jsonapi = self.content["data"][0]
        people_jsonapi = {
            included["id"]: included
            for included in self.content["included"]
            if included["type"] == "people"}
        author_jsonapi = people_jsonapi[
            article_jsonapi["relationships"]["author"]["data"]["id"]]
        comments_jsonapi = {
            included["id"]: included
            for included in self.content["included"]
            if included["type"] == "comments"}

        person_uuids = {
            comment_jsonapi["relationships"]["author"]["data"]["id"]
            for comment_jsonapi in comments_jsonapi.values()}
        self.author = models.Person.objects.create(
            uuid=author_jsonapi["id"],
            **utils.to_kwargs(author_jsonapi["attributes"]))
        person_uuids.remove(author_jsonapi["id"])
        models.Person.objects.bulk_create([
            models.Person(uuid=person_uuid) for person_uuid in person_uuids])
        self.article = models.Article.objects.create(
            uuid=article_jsonapi["id"], author=self.author,
            **utils.to_kwargs(article_jsonapi["attributes"]))
        self.comments = models.Comment.objects.bulk_create([
            models.Comment(
                uuid=comment_id, article=self.article, author=self.author,
                **utils.to_kwargs(comment_jsonapi["attributes"])) for
            comment_id, comment_jsonapi in comments_jsonapi.items()])
