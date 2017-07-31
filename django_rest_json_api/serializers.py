"""
DRF serializers implementing the various JSON API objects.
"""

import collections.abc
import collections

from django.utils import six

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.utils import html

link_url_field = serializers.URLField(
    label='Link URL', help_text='a string containing the link’s URL',
    required=True)


class JSONAPIResourceIdentifierSerializer(serializers.Serializer):
    """
    Common serializer support for JSON API objects with resource identifiers.
    """

    # A resource object MUST contain at least the following top-level members:
    id = serializers.CharField(
        label='Resource Identifier',
        help_text='a specific identifier within this type of resource',
        required=True)
    type = serializers.CharField(
        label='Resource Type',
        help_text='the type of this resource',
        required=True)


class JSONAPIMetaContainerSerializer(serializers.Serializer):
    """
    Common serializer support for objects with a non-standard `meta` key.
    """

    meta = serializers.DictField(
        label='Meta Object',
        help_text='a meta object that contains non-standard meta-information.',
        required=False)


class JSONAPILinkSerializer(JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API link object.
    """

    href = serializers.URLField(
        label='Link URL', help_text="a string containing the link’s URL.",
        required=True)

    def to_internal_value(self, data):
        """
        Optionally accept a URL directly.
        """
        if not isinstance(data, collections.abc.Mapping):
            return link_url_field.to_internal_value(data)
        return super(JSONAPILinkSerializer, self).to_internal_value(data)


class JSONAPILinksSerializer(serializers.Serializer):
    """
    Serializer for a JSON API links object.
    """

    self = JSONAPILinkSerializer(
        label='Document Link',
        help_text='a link for the resource itself',
        required=False)
    related = JSONAPILinkSerializer(
        label='Related Resource Link',
        help_text='a related resource link',
        required=False)

    # Pagination links
    first = serializers.URLField(
        label='First Page', help_text='the first page of data',
        required=False)
    last = serializers.URLField(
        label='Last Page', help_text='the last page of data',
        required=False)
    prev = serializers.URLField(
        label='Prev Page', help_text='the previous page of data',
        required=False)
    next = serializers.URLField(
        label='Next Page', help_text='the next page of data',
        required=False)


class JSONAPILinkableSerializer(serializers.Serializer):
    """
    Common serializer support for JSON API objects with links.
    """

    links = JSONAPILinksSerializer(
        label='Links',
        help_text='a links object containing links related to the resource.',
        required=False)


class JSONAPIRelationshipsSerializer(serializers.DictField):
    """
    Serializer for a JSON API relationships container object.
    """

    def to_internal_value(self, data):
        """
        Handle resource collections where 'data' is an array.
        """
        if html.is_html_input(data):
            data = html.parse_html_dict(data)
        if not isinstance(data, dict):
            self.fail('not_a_dict', input_type=type(data).__name__)

        value = {}
        collection_child = type(self.child)(
            *self.child._args, **self.child._kwargs)
        data_field = collection_child.fields['data']
        collection_child.fields['data'] = type(data_field)(
            *data_field._args, many=True, **data_field._kwargs)
        for relationship_name, relationship_resource in data.items():
            child = self.child
            if (
                    isinstance(
                        relationship_resource,
                        collections.abc.Mapping) and
                    isinstance(
                        relationship_resource.get('data', {}),
                        collections.abc.Sequence)):
                child = collection_child
            value[six.text_type(relationship_name)] = child.run_validation(
                relationship_resource)
        return value


class JSONAPIRelationshipSerializer(
        JSONAPILinkableSerializer, JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API relationship object.
    """

    MUST_HAVE_ONE_OF = ('links', 'data', 'meta')

    data = JSONAPIResourceIdentifierSerializer(
        label='Resource', help_text='the document\'s "primary data"',
        required=False)

    default_error_messages = {
        'missing_must': (
            'A "relationship object" MUST contain at least '
            'one of the following: `links`, `data`, `meta`.'),
    }

    def validate(self, attrs):
        """
        JSON API relationship validation.
        """
        if not set(attrs).intersection(self.MUST_HAVE_ONE_OF):
            self.fail('missing_must')
        return attrs


class JSONAPIResourceSerializer(
        JSONAPIResourceIdentifierSerializer, JSONAPILinkableSerializer,
        JSONAPIMetaContainerSerializer):
    """
    Serializer for the JSON API specific aspects of a resource.
    """

    default_error_messages = {
        'reserved_field': (
            'A resource can not have {member!r} fields named: {fields}.'),
        'field_conflicts': (
            'A resource can not have `attributes` and `relationships` '
            'with the same name: {fields}.'),
    }

    # In addition, a resource object MAY contain any of these top-level
    # members:
    attributes = serializers.DictField(
        label='Resource Attributes',
        help_text='an object representing some of the resource’s data.',
        required=False)
    relationships = JSONAPIRelationshipsSerializer(
        label='Related Resources',
        help_text='a relationships object describing relationships '
        'between the resource and other JSON API resources.',
        required=False, child=JSONAPIRelationshipSerializer())

    def validate(self, attrs):
        """
        JSON API Resource validation.
        """
        errors = collections.OrderedDict()

        attributes = set(attrs.get('attributes', {}))
        relationships = set(attrs.get('relationships', {}))
        for member, keys in (
                ('attributes', attributes), ('relationships', relationships)):
            reserved = keys.intersection(('type', 'id'))
            if reserved:
                try:
                    self.fail(
                        'reserved_field', member=member,
                        fields=', '.join(repr(field) for field in reserved))
                except exceptions.ValidationError as exc:
                    errors[member] = exc.detail
                    continue

        conflicts = keys.intersection(('type', 'id'))
        if conflicts:
            try:
                self.fail('field_conflicts', fields=', '.join(repr(
                    field) for field in conflicts))
            except exceptions.ValidationError as exc:
                errors["attributes"] = exc.detail

        if errors:
            raise exceptions.ValidationError(errors)

        return attrs


class JSONAPIErrorLinksSerializer(serializers.Serializer):
    """
    Serializer for a JSON API error links object.
    """

    about = JSONAPILinkSerializer(
        label='Error Detail Link',
        help_text='a link that leads to further details '
        'about this particular occurrence of the problem.',
        required=False)


class JSONAPIErrorSourceSerializer(serializers.Serializer):
    """
    Serializer for a JSON API error source object.
    """

    # TODO validator
    pointer = serializers.CharField(
        label='Error Pointer',
        help_text='a JSON Pointer [RFC6901] to the associated entity in the '
        'request document [e.g. "/data" for a primary data object, or '
        '"/data/attributes/title" for a specific attribute].',
        required=False)
    parameter = serializers.CharField(
        label='Error Parameter',
        help_text='a string indicating which '
        'URI query parameter caused the error.',
        required=False)


class JSONAPIErrorSerializer(JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API error object.
    """

    id = serializers.CharField(
        label='Error ID',
        help_text='a unique identifier for '
        'this particular occurrence of the problem.',
        required=False)
    links = JSONAPIErrorLinksSerializer(
        label='Error Links',
        help_text='a links object containing further details '
        'about this particular occurrence of the problem.',
        required=False)
    status = serializers.IntegerField(
        label='Error Status',
        help_text='the HTTP status code applicable to this problem, '
        'expressed as a string value.',
        required=False, max_value=599, min_value=100)
    code = serializers.CharField(
        label='Application Error Code',
        help_text='an application-specific error code, '
        'expressed as a string value.',
        required=False)
    title = serializers.CharField(
        label='Error Ttle',
        help_text='a short, human-readable summary of the problem that '
        'SHOULD NOT change from occurrence to occurrence of the problem, '
        'except for purposes of localization.',
        required=False)
    detail = serializers.CharField(
        label='Error Detail',
        help_text='a human-readable explanation specific to this occurrence '
        'of the problem. Like title, this field’s value can be localized.',
        required=False)
    source = JSONAPIErrorSourceSerializer(
        label='Error Source',
        help_text='an object containing references '
        'to the source of the error.',
        required=False)


class JSONAPIImplementationSerializer(JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API implementation detail object.
    """

    version = serializers.CharField(
        label='JSON API Version',
        help_text='the highest JSON API version supported.',
        required=False, default='1.0')


class JSONAPIDocumentSerializer(
        JSONAPILinkableSerializer, JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API top-level document.
    """

    default_error_messages = {
        'errors_and_data': (
            'The members data and errors '
            'MUST NOT coexist in the same document.'),
        'missing_must': (
            'A document MUST contain at least one of '
            'the following top-level members: `data`, `errors`, `meta`.'),
        'included_wo_data': (
            'If a document does not contain a top-level data key, '
            'the included member MUST NOT be present either.'),
        'duplicate_resource': (
            'A document MUST NOT include more than one resource object '
            'for each type ({type!r}) and id ({id!r}) pair, '
            'duplicate found in {member!r}.'),
    }

    # A document MUST contain at least one of the following top-level members
    data = JSONAPIResourceSerializer(
        label='Resource', help_text='the document\'s "primary data"',
        required=False)
    errors = serializers.ListField(
        label='Errors', help_text='an array of error objects',
        required=False, child=JSONAPIErrorSerializer(
            label='Error', help_text='an error object'))

    # A document MAY contain any of these top-level members:
    jsonapi = JSONAPIImplementationSerializer(
        label='JSON API Implementation',
        help_text="an object describing the server's implementation",
        required=False)
    included = serializers.ListField(
        label='Included Related Resources',
        help_text='an array of resource objects that are related '
        'to the primary data and/or each other ("included resources").',
        child=JSONAPIResourceSerializer(
            label='Included Related Resource',
            help_text='a resource object that is related to the primary data '
            'and/or other included resources/'),
        required=False)

    def __init__(self, instance=None, data=serializers.empty, **kwargs):
        """
        Handle resource collections where 'data' is an array.
        """
        super(JSONAPIDocumentSerializer, self).__init__(
            instance=instance, data=data, **kwargs)

        if isinstance(data.get('data', {}), collections.abc.Sequence):
            data_field = self.fields['data']
            self.fields['data'] = type(data_field)(
                *data_field._args, many=True, **data_field._kwargs)

    def validate(self, attrs):
        """
        JSON API Document-wide validation.
        """
        errors = collections.OrderedDict()

        if 'errors' in attrs and 'data' in attrs:
            try:
                self.fail('errors_and_data')
            except exceptions.ValidationError as exc:
                errors["attributes"] = exc.detail
        if not ('data' in attrs or 'errors' in attrs or 'meta' in attrs):
            try:
                self.fail('missing_must')
            except exceptions.ValidationError as exc:
                errors["attributes"] = exc.detail

        if 'included' in attrs and 'data' not in attrs:
            try:
                self.fail('included_wo_data')
            except exceptions.ValidationError as exc:
                errors["attributes"] = exc.detail
        resource_ids = set()
        data = attrs.get('data', [])
        if not isinstance(data, collections.abc.Sequence):
            data = [data]
        for member, resources in (
                ('data', data), ('included', attrs.get('included', []))):
            for resource in resources:
                type_id = (resource["type"], resource["id"])
                if type_id in resource_ids:
                    try:
                        self.fail(
                            'duplicate_resource',
                            member=member, type=type_id[0], id=type_id[1])
                    except exceptions.ValidationError as exc:
                        errors['/{0}/{1}/{2}'.format(
                            member, *type_id)] = exc.detail
                resource_ids.add(type_id)

        if errors:
            raise exceptions.ValidationError(errors)

        return attrs
