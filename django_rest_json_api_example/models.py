"""
Django ORM models for the JSON API examples.
"""

from django.db import models


class Person(models.Model):
    """
    JSON API example person model.
    """

    uuid = models.UUIDField()
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)


class Article(models.Model):
    """
    JSON API example article model.
    """

    uuid = models.UUIDField()
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Person, blank=False)


class Comment(models.Model):
    """
    JSON API example comment model.
    """

    uuid = models.UUIDField()
    body = models.TextField()
    article = models.ForeignKey(Article, blank=False, related_name='comments')
    author = models.ForeignKey(Person, blank=False)
