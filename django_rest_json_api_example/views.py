from drf_extra_fields import serializer_formats as viewsets

from django_rest_json_api_example import models
from django_rest_json_api_example import serializers


class PeopleViewSet(viewsets.UUIDModelViewSet):
    """
    JSON API example authors endpoint.
    """
    queryset = models.Person.objects.all().order_by('-date_joined')
    serializer_class = serializers.PersonSerializer


class ArticlesViewSet(viewsets.UUIDModelViewSet):
    """
    JSON API example articles endpoint.
    """
    queryset = models.Article.objects.all()
    serializer_class = serializers.ArticleSerializer


class CommentsViewSet(viewsets.UUIDModelViewSet):
    """
    JSON API example comments endpoint.
    """
    queryset = models.Comment.objects.all()
    serializer_class = serializers.CommentSerializer
