"""
DRF serializers implementing the various JSON API objects.
"""

import collections
try:
    from collections import abc as collections_abc
except ImportError:  # pragma: no cover
    # BBB Python 2 compat
    collections_abc = collections

import pkg_resources

from django.db import models
from django.utils import functional

from rest_framework.settings import api_settings
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework import relations

from drf_extra_fields import parameterized


class JSONAPIPrimaryDataSerializer(
        parameterized.ParameterizedGenericSerializer):
    """
    Support JSON API primary `data` objects as either single or an array.
    """

    # A resource object MUST contain at least the following top-level members:
    id = serializers.UUIDField(
        label='Resource Identifier',
        help_text='a specific identifier within this type of resource',
        required=True)
    type = parameterized.SerializerParameterField(
        label='Resource Type',
        help_text='the type of this resource',
        required=True)

    @functional.cached_property
    def many_serializer(self):
        """
        Construct a list serializer on-demand for multiple values.
        """
        many = type(self).many_init(*self._args, **self._kwargs)
        if self.field_name is not None:
            many.bind(self.field_name, self.parent)
        return many

    def get_value(self, dictionary):
        """
        Use the list serializer for multiple resources.
        """
        value = super(
            JSONAPIPrimaryDataSerializer, self).get_value(dictionary)
        if isinstance(value, list):
            return self.many_serializer.get_value(dictionary)
        return value

    def run_validation(self, data=serializers.empty):
        """
        Use the list serializer for multiple resources.
        """
        if isinstance(data, list):
            return self.many_serializer.run_validation(data)
        return super(
            JSONAPIPrimaryDataSerializer, self).run_validation(data)

    def to_internal_value(self, data):
        """
        Use the list serializer for multiple resources.
        """
        if isinstance(data, list):
            return self.many_serializer.to_internal_value(data)
        return super(
            JSONAPIPrimaryDataSerializer, self).to_internal_value(data)

    def to_representation(self, instance):
        """
        Use the list serializer for multiple resources.
        """
        if isinstance(instance, (list, models.QuerySet)):
            return self.many_serializer.to_representation(instance)
        return super(
            JSONAPIPrimaryDataSerializer, self).to_representation(
                instance)

    def validate(self, attrs):
        """
        Use the list serializer for multiple resources.
        """
        if isinstance(attrs, list):
            return self.many_serializer.validate(attrs)
        return super(JSONAPIPrimaryDataSerializer, self).validate(
            attrs)

    def update(self, instance, validated_data):
        """
        Use the list serializer for multiple resources.
        """
        if isinstance(validated_data, list):
            return self.many_serializer.update(instance, validated_data)
        return super(JSONAPIPrimaryDataSerializer, self).update(
            instance, validated_data)

    def create(self, validated_data):
        """
        Use the list serializer for multiple resources.
        """
        if isinstance(validated_data, list):
            return self.many_serializer.create(validated_data)
        return super(JSONAPIPrimaryDataSerializer, self).create(
            validated_data)

    def save(self, **kwargs):
        """
        Use the list serializer for multiple resources.
        """
        if isinstance(self.validated_data, list):
            # Guard against incorrect use of `serializer.save(commit=False)`
            assert 'commit' not in kwargs, (
                "'commit' is not a valid keyword argument to the 'save()' "
                "method. If you need to access data before committing to the "
                "database then inspect 'serializer.validated_data' "
                "instead. You can also pass additional keyword arguments to "
                "'save()' if you need to set extra attributes on the saved "
                "model instance. For example: "
                "'serializer.save(owner=request.user)'.'"
            )

            validated_data = []
            for child_data in self.validated_data:
                # Use copy() to preserve specific serializer reference
                child_data = child_data.copy()
                child_data.update(kwargs)
                validated_data.append(child_data)

            if self.instance is not None:
                self.instance = self.update(self.instance, validated_data)
                assert self.instance is not None, (  # pragma: no cover
                    '`update()` did not return an object instance.'
                )
            else:
                self.instance = self.create(validated_data)
                assert self.instance is not None, (
                    '`create()` did not return an object instance.'
                )

            return self.instance
        return super(JSONAPIPrimaryDataSerializer, self).save(**kwargs)

    def is_valid(self, raise_exception=False):
        """
        Use the list serializer for multiple resources.
        """
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )

        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except exceptions.ValidationError as exc:
                if isinstance(self.initial_data, list):
                    self._validated_data = []
                else:
                    self._validated_data = {}
                self._errors = exc.detail
            else:
                if isinstance(self.initial_data, list):
                    self._errors = []
                else:
                    self._errors = {}

        if self._errors and raise_exception:
            raise exceptions.ValidationError(self.errors)

        return not bool(self._errors)

    @property
    def data(self):
        """
        Use the list serializer for multiple resources.
        """
        data = super(serializers.Serializer, self).data
        if isinstance(data, list):
            return serializers.ReturnList(data, serializer=self)
        else:
            return serializers.ReturnDict(data, serializer=self)

    @property
    def errors(self):
        """
        Use the list serializer for multiple resources.
        """
        errors = super(serializers.Serializer, self).errors
        if isinstance(errors, list):
            return serializers.ReturnList(
                errors, serializer=self.many_serializer)
        else:
            return errors


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
        label='Link URL', help_text="a string containing the link's URL.",
        required=True)

    def to_internal_value(self, data):
        """
        Optionally accept a URL directly.
        """
        if not isinstance(data, collections_abc.Mapping):
            return self.fields['href'].to_internal_value(data)
        return super(JSONAPILinkSerializer, self).to_internal_value(data)

    def to_representation(self, instance):
        """
        Optionally return a URL directly.
        """
        if not isinstance(instance, collections_abc.Mapping):
            return self.fields['href'].to_representation(instance)
        return super(JSONAPILinkSerializer, self).to_representation(instance)


class JSONAPILinksSerializer(serializers.Serializer):
    """
    Serializer for a JSON API links object.
    """

    # TODO use hyperlinked field for `href`
    self = JSONAPILinkSerializer(
        label='Document Link',
        help_text='a link for the resource itself',
        required=False)
    related = JSONAPILinkSerializer(
        label='Related Resource Link',
        help_text='a related resource link',
        required=False)

    # Pagination links
    # TODO integrate with DRF pagination
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


class JSONAPIResourceIdentifierSerializer(JSONAPIPrimaryDataSerializer):
    """
    Common serializer support for JSON API objects with resource identifiers.
    """

    # Use just `type` and `id`
    skip_parameterized = False
    exclude_parameterized = True

    def to_internal_value(self, data):
        """
        Translate JSON API resource identifier to the ID DRF expects.
        """
        value = super(
            JSONAPIResourceIdentifierSerializer, self).to_internal_value(data)
        if isinstance(value, list):
            return value

        return value.clone.fields['id'].get_attribute(value)


class JSONAPIRelationshipSerializer(
        JSONAPILinkableSerializer, JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API relationship object.
    """

    MUST_HAVE_ONE_OF = ('links', 'data', 'meta')

    data = JSONAPIResourceIdentifierSerializer(
        label='Resource', help_text='the document\'s "primary data"',
        required=False, partial=True)

    default_error_messages = {
        'missing_must': (
            'A "relationship object" MUST contain at least '
            'one of the following: `links`, `data`, `meta`.'),
    }

    def to_internal_value(self, data):
        """
        Translate JSON API relationship representation to what DRF consumes.
        """
        if not set(data).intersection(self.MUST_HAVE_ONE_OF):
            self.fail('missing_must')
        value = super(
            JSONAPIRelationshipSerializer, self).to_internal_value(data)
        # Return only the primary data
        return self.fields['data'].get_attribute(value)


class JSONAPIResourceSerializer(
        JSONAPIPrimaryDataSerializer, JSONAPILinkableSerializer,
        JSONAPIMetaContainerSerializer):
    """
    Serializer for the JSON API specific aspects of a resource.
    """

    RESERVED_FIELDS = {'type', 'id'}

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
        help_text="an object representing some of the resource's data.",
        required=False)
    relationships = serializers.DictField(
        label='Related Resources',
        help_text='a relationships object describing relationships '
        'between the resource and other JSON API resources.',
        required=False, child=JSONAPIRelationshipSerializer())

    def to_internal_value(self, data):
        """
        Translate the JSON API format into the DRF internal format.
        """
        if isinstance(data, list):
            return super(
                JSONAPIResourceSerializer, self).to_internal_value(data)

        # Do validation here while it's still in JSON API format
        errors = collections.OrderedDict()

        attributes = self.fields['attributes'].get_value(data)
        if attributes is serializers.empty:
            value = {}
        else:
            value = attributes.copy()
        relationships = self.fields['relationships'].get_value(data)
        if relationships is not serializers.empty:
            relationships_value = self.fields[
                'relationships'].to_internal_value(relationships)
        for member, jsonapi in (
                ('attributes', value), ('relationships', relationships)):
            if jsonapi is serializers.empty:
                continue
            reserved = self.RESERVED_FIELDS.intersection(jsonapi)
            if reserved:
                try:
                    self.fail(
                        'reserved_field', member=member,
                        fields=', '.join(repr(field) for field in reserved))
                except exceptions.ValidationError as exc:
                    errors[member] = exc.detail
                    continue

        if serializers.empty not in [value, relationships]:
            conflicts = set(value).intersection(relationships)
            if conflicts:
                try:
                    self.fail('field_conflicts', fields=', '.join(repr(
                        field) for field in conflicts))
                except exceptions.ValidationError as exc:
                    errors["attributes"] = exc.detail

        if errors:
            raise exceptions.ValidationError(errors)

        value["type"] = self.fields['type'].get_value(data)
        value["id"] = self.fields['id'].get_value(data)

        # Lookup the per-type serializer so we can introspect related fields
        self.clone_meta['parameter_field'].to_internal_value(
            self.clone_meta['parameter_field'].get_value(data))
        specific = self.clone_meta[
            'parameter_field'].clone_specific_internal(data)

        if relationships is serializers.empty:
            return super(
                JSONAPIResourceSerializer, self).to_internal_value(value)

        # Move items from the `relationships` object and insert them into the
        # main object as DRF expects internally
        for field in specific.fields.values():

            if (
                    isinstance(field, (
                        relations.RelatedField,
                        relations.ManyRelatedField)) and
                    field.field_name in relationships_value):
                value[field.field_name] = field.get_attribute(
                    relationships_value)

        return super(JSONAPIResourceSerializer, self).to_internal_value(value)

    def to_representation(self, instance):
        """
        Translate the DRF internal format into the JSON API format.
        """
        data = super(JSONAPIResourceSerializer, self).to_representation(
            instance)
        if isinstance(instance, list):
            return data

        relationships_data = collections.OrderedDict()
        for field in data.clone.fields.values():
            if isinstance(field, (
                    relations.RelatedField, relations.ManyRelatedField)):
                relationship_instance = field.to_internal_value(
                    field.get_value(data))
                relationships_data[field.field_name] = self.fields[
                    "relationships"].child.to_representation(
                        {"data": relationship_instance})
                data.pop(field.field_name)

        resource = collections.OrderedDict()
        resource["type"] = data.pop("type")
        resource["id"] = data.pop("id")
        if data:
            resource["attributes"] = data
        if relationships_data:
            resource["relationships"] = relationships_data

        return resource


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
        help_text="a human-readable explanation specific to this occurrence "
        "of the problem. Like title, this field's value can be localized.",
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

    default_error_messages = {
        'version_too_high': (
            'The JSON API version requested is too high and not supported'
            ': {version}.'),
    }

    version = serializers.CharField(
        label='JSON API Version',
        help_text='the highest JSON API version supported.',
        required=False, default=pkg_resources.parse_version('1.0'))

    def validate_version(self, version):
        """
        The version must be less than or equal to our version.
        """
        parsed = pkg_resources.parse_version(version)
        if parsed > self.fields['version'].get_default():
            self.fail('version_too_high', version=parsed)
        return parsed


class JSONAPIDocumentSerializer(
        JSONAPILinkableSerializer, JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API top-level document.
    """

    MUST_HAVE_ONE_OF = {'data', 'errors', 'meta'}

    default_error_messages = {
        'errors_and_data': (
            'The members data and errors '
            'MUST NOT coexist in the same document.'),
        'missing_must': (
            'A document MUST contain at least one of '
            'the following top-level members: `data`, `errors`, `meta`.'),
        'included_wo_data': (
            'If a document does not contain a top-level data key, '
            'the `included` member MUST NOT be present either.'),
        'included_to_internal': (
            'A document may not contain `included` resrouces on '
            'incomming/write requrests: POST, PUT, PATCH, DELETE.'),
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
        required=False, default={})
    included = serializers.ListField(
        label='Included Related Resources',
        help_text='an array of resource objects that are related '
        'to the primary data and/or each other ("included resources").',
        child=JSONAPIResourceSerializer(
            label='Included Related Resource',
            help_text='a resource object that is related to the primary data '
            'and/or other included resources/'),
        required=False)

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        Don't use the ListSerializer, delegate to the `data` serializer.
        """
        return super(JSONAPIDocumentSerializer, cls).__new__(
            cls, *args, **kwargs)

    def to_internal_value(self, data):
        """
        JSON API Document-wide validation.
        """
        # Do validation here while we still have the JSON API format
        errors = collections.OrderedDict()

        errors_value = self.fields['errors'].get_value(data)
        data_value = self.fields['data'].get_value(data)
        if (
                errors_value is not serializers.empty and
                data_value is not serializers.empty):
            try:
                self.fail('errors_and_data')
            except exceptions.ValidationError as exc:
                errors[api_settings.NON_FIELD_ERRORS_KEY] = exc.detail
        if not self.MUST_HAVE_ONE_OF.intersection(data):
            try:
                self.fail('missing_must')
            except exceptions.ValidationError as exc:
                errors[api_settings.NON_FIELD_ERRORS_KEY] = exc.detail

        included = self.fields['included'].get_value(data)
        if included is not serializers.empty:
            try:
                self.fail('included_to_internal')
            except exceptions.ValidationError as exc:
                errors["included"] = exc.detail

        self._validate_duplicates(data, errors)

        if errors:
            raise exceptions.ValidationError(errors)

        value = super(JSONAPIDocumentSerializer, self).to_internal_value(data)
        try:
            return self.fields['data'].get_attribute(value)
        except serializers.SkipField:
            return self.fields['errors'].get_attribute(value)

    def to_representation(self, instance):
        """
        Place the instance into the `data` key.
        """
        data = super(JSONAPIDocumentSerializer, self).to_representation(
            {"data": instance})

        errors = collections.OrderedDict()

        self._validate_duplicates(
            data, errors, ('included', data.get('included', [])))

        if errors:
            raise exceptions.ValidationError(errors)

        return data

    def _validate_duplicates(self, data, errors, *member_resources):
        """
        Check for duplicate resources.
        """
        resource_ids = set()
        primary = data.get('data', [])
        if not isinstance(primary, list):
            primary = [primary]
        for member, resources in (('data', primary), ) + member_resources:
            for resource in resources:
                type_id = (
                    # Lookup the type and ID from the resource fields
                    self.fields['data'].fields['type'].get_value(resource),
                    self.fields['data'].fields['id'].get_value(resource))
                if type_id in resource_ids:
                    try:
                        self.fail(
                            'duplicate_resource',
                            member=member, type=type_id[0], id=type_id[1])
                    except exceptions.ValidationError as exc:
                        errors['/{0}/{1}/{2}'.format(
                            member, *type_id)] = exc.detail
                resource_ids.add(type_id)
        return resource_ids
