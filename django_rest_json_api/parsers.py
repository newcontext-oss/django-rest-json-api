from rest_framework import parsers

from . import renderers


class JSONAPIParser(parsers.JSONParser):
    """
    JSON API format parser.
    """
    media_type = renderers.JSONAPIRenderer.media_type
    renderer_class = renderers.JSONAPIRenderer

    serializer_class = renderers.JSONAPIRenderer.serializer_class
    error_serializer_class = renderers.JSONAPIRenderer.error_serializer_class
