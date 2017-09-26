"""
Django ORM models for the JSON API examples.
"""

import uuid

from django.db import models


class Person(models.Model):
    """
    JSON API example person model.
    """

    uuid = models.UUIDField(default=uuid.uuid4())
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)


class Article(models.Model):
    """
    JSON API example article model.
    """

    uuid = models.UUIDField(default=uuid.uuid4())
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(Person, null=True, blank=True)


class Comment(models.Model):
    """
    JSON API example comment model.
    """
    class Meta:
        ordering = ["uuid"]

    uuid = models.UUIDField(default=uuid.uuid4())
    body = models.TextField()
    article = models.ForeignKey(Article, blank=False, related_name='comments')
    author = models.ForeignKey(Person, blank=False)
