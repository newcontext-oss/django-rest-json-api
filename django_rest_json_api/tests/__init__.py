"""
Django REST JSON API tests.
"""

from test_har import django_rest_har as test_har

import re

from django.core import validators

from rest_framework import request
from rest_framework import reverse
from rest_framework import test

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
        self.author_jsonapi = people_jsonapi[
            article_jsonapi["relationships"]["author"]["data"]["id"]]
        comments_jsonapi = {
            included["id"]: included
            for included in self.content["included"]
            if included["type"] == "comments"}

        # TODO Adjust relationship links until DRF nested routers are
        # implemented
        del self.content["links"]["next"]
        del self.content["links"]["last"]
        self.included = self.content.pop("included")
        del article_jsonapi["relationships"]["author"]["links"]["self"]
        article_jsonapi["relationships"]["author"]["links"][
            "related"] = self.author_jsonapi["links"]["self"]
        del article_jsonapi["relationships"]["comments"]["links"]["self"]
        article_jsonapi["relationships"]["comments"]["links"][
            "related"] = 'http://testserver/comments/'

        person_uuids = {
            comment_jsonapi["relationships"]["author"]["data"]["id"]
            for comment_jsonapi in comments_jsonapi.values()}
        self.author = models.Person.objects.create(
            uuid=self.author_jsonapi["id"],
            **utils.to_kwargs(self.author_jsonapi["attributes"]))
        person_uuids.remove(self.author_jsonapi["id"])
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

        self.factory = test.APIRequestFactory()
        self.article_request = request.Request(self.factory.post(
            reverse.reverse(
                models.Article._meta.model_name + '-detail',
                kwargs=dict(uuid=self.article.uuid))))
        self.articles_request = request.Request(self.factory.post(
            reverse.reverse(models.Article._meta.model_name + '-list')))
