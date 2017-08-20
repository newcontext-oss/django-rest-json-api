from drf_extra_fields import relations

from django_rest_json_api_example import models


class PersonSerializer(relations.UUIDModelSerializer):
    """
    JSON API example serializer for author relationships.
    """

    class Meta(relations.UUIDModelSerializer.Meta):
        model = models.Person


class ArticleSerializer(relations.UUIDModelSerializer):
    """
    JSON API example serializer for articles.
    """

    class Meta(relations.UUIDModelSerializer.Meta):
        model = models.Article
        exclude = None
        fields = ('id', 'title', 'author', 'comments')


class CommentSerializer(relations.UUIDModelSerializer):
    """
    JSON API example serializer for comments.
    """

    class Meta(relations.UUIDModelSerializer.Meta):
        model = models.Comment
