from rest_framework import renderers

from . import serializers


class JSONAPIRenderer(renderers.JSONRenderer):
    """
    JSON API format renderer.
    """
    media_type = 'application/vnd.api+json'
    format = 'json-api'

    serializer_class = serializers.JSONAPIDocumentSerializer
    pagination_serializer_class = serializers.JSONAPIPaginationSerializer
    error_serializer_class = serializers.JSONAPIDocumentSerializer
