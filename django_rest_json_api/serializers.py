"""
DRF serializers describing and implementing the JSON API format.
"""

import operator
import collections
try:
    from collections import abc as collections_abc
except ImportError:  # pragma: no cover
    # BBB Python 2 compat
    collections_abc = collections

import pkg_resources

import inflection

from django.db import models
from django.utils import functional
from django.utils import six

from rest_framework.settings import api_settings
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework import relations

from drf_extra_fields import generic
from drf_extra_fields import parameterized

reverse_inflectors = {
    inflection.singularize: inflection.pluralize,
    inflection.pluralize: inflection.singularize,
    inflection.dasherize: inflection.underscore,
    inflection.underscore: inflection.dasherize,
    inflection.parameterize: inflection.underscore,
}
field_inflectors = [inflection.parameterize]


def flatten_error_details(data, source=''):
    """
    Recursively flatten nested error details into an array.

    Based on `rest_framework.exceptions._get_error_details()`.
    """
    if isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, exceptions.ErrorDetail):
                # Don't index multiple errors for the same source
                item_source = source
            else:
                item_source = '{0}/{1}'.format(source, idx)
            for recursed_source, recursed_item in flatten_error_details(
                    item, source=item_source):
                yield (recursed_source, recursed_item)
    elif isinstance(data, dict):
        for key, value in sorted(data.items(), key=operator.itemgetter(0)):
            for recursed_source, recursed_value in flatten_error_details(
                    value, source='{0}/{1}'.format(source, key)):
                yield (recursed_source, recursed_value)
    else:
        yield source, data


class JSONAPIPrimaryDataSerializer(
        parameterized.ParameterizedGenericSerializer):
    """
    Support JSON API primary `data` objects as either single or an array.
    """

    # A resource object MUST contain at least the following top-level members:
    id = serializers.UUIDField(
        label='Resource Identifier',
        help_text='a specific identifier within this type of resource',
        required=False)
    type = parameterized.SerializerParameterField(
        label='Resource Type',
        help_text='the type of this resource',
        required=True, source="*")

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


class JSONAPIResourceIdentifierSerializer(JSONAPIPrimaryDataSerializer):
    """
    Common serializer support for JSON API objects with resource identifiers.
    """

    primary = False
    # Include only `type` and `id`
    exclude_parameterized = True

    def to_internal_value(self, data):
        """
        Return only the ID.
        """
        value = super(
            JSONAPIResourceIdentifierSerializer, self).to_internal_value(data)

        # Get the ID field from the specific serializer
        id_field = list(value.serializer.fields.values())[0]
        # Return only the ID as DRF expects for relationships
        return id_field.get_attribute(value)


class JSONAPIMetaContainerSerializer(serializers.Serializer):
    """
    Common serializer support for objects with a non-standard `meta` key.
    """

    meta = serializers.DictField(
        label='Meta Object',
        help_text='a meta object that contains non-standard meta-information.',
        required=False, read_only=True)


class JSONAPILinkSerializer(JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API link object.
    """

    # The common case in the JSON API examples is for links to be simple
    # string URLs, so default to that.
    # TODO take from app settings
    as_url_string = True

    href = generic.HyperlinkedGenericRelationsField(
        label='Link URL', help_text="a string containing the link's URL.",
        lookup_field='uuid', required=True)

    def __init__(
            self, instance=None, data=serializers.empty,
            as_url_string=None, **kwargs):
        """
        Support specifying whether to use a flat URL string.
        """
        super(JSONAPILinkSerializer, self).__init__(
            instance=instance, data=data, **kwargs)
        if as_url_string is not None:
            self.as_url_string = as_url_string

    def to_internal_value(self, data):
        """
        Optionally accept a URL directly.
        """
        if not isinstance(data, collections_abc.Mapping):
            data = {"href": data}
        return self.fields['href'].get_attribute(
            super(JSONAPILinkSerializer, self).to_internal_value(data))

    def to_representation(self, instance):
        """
        Optionally return a URL directly.
        """
        data = super(JSONAPILinkSerializer, self).to_representation(instance)
        if self.as_url_string:
            data = self.fields['href'].get_value(data)
        return data


class JSONAPIPaginationLinksSerializer(serializers.Serializer):
    """
    The JSON API links required (MUST) for pagination.
    """

    # Pagination links
    first = JSONAPILinkSerializer(
        label='First Page', help_text='the first page of data',
        required=False)
    last = JSONAPILinkSerializer(
        label='Last Page', help_text='the last page of data',
        required=False)
    prev = JSONAPILinkSerializer(
        label='Prev Page', help_text='the previous page of data',
        required=False, source='previous')
    next = JSONAPILinkSerializer(
        label='Next Page', help_text='the next page of data',
        required=False)


class JSONAPILinksSerializer(JSONAPIPaginationLinksSerializer):
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

    def to_representation(self, instance):
        """
        Move the ID field out of the attributes.
        """
        instance = getattr(
            getattr(instance, 'serializer', None), 'instance', instance)

        if isinstance(self.parent, JSONAPIRelationshipSerializer):
            link_field = self.fields['related']
            # TODO `self` link for the relationship itself
        else:
            link_field = self.fields['self']

        link_value = collections.OrderedDict()
        if isinstance(self.parent, JSONAPIDocumentSerializer):
            if 'request' in self.context:
                # Use the current view for the link
                serializers.set_value(
                    link_value, link_field.fields['href'].source_attrs,
                    # Reconstitute an "instance" from the request url
                    link_field.fields['href'].to_internal_value(
                        self.context['request'].get_raw_uri()))
        else:
            serializers.set_value(
                link_value, link_field.fields['href'].source_attrs, instance)

        value = collections.OrderedDict()
        serializers.set_value(
            value, link_field.source_attrs, link_value)

        return super(JSONAPILinksSerializer, self).to_representation(value)


class JSONAPILinkableSerializer(serializers.Serializer):
    """
    Common serializer support for JSON API objects with links.
    """

    links = JSONAPILinksSerializer(
        label='Links',
        help_text='a links object containing links related to the resource.',
        required=False, read_only=True, source="*")


class JSONAPIRelationshipSerializer(
        JSONAPILinkableSerializer, JSONAPIMetaContainerSerializer):
    """
    Serializer for a JSON API relationship object.
    """

    MUST_HAVE_ONE_OF = ('links', 'data', 'meta')

    data = JSONAPIResourceIdentifierSerializer(
        label='Resource', help_text='the relationship\'s "primary data"',
        required=False, partial=True)

    # Have to override not to use `source="*"` because relationship objects
    # require manual handling of `data`
    links = JSONAPILinksSerializer(
        label='Links',
        help_text='a links object containing links related to the resource.',
        required=False, read_only=True)

    default_error_messages = {
        'missing_must': (
            'A "relationship object" MUST contain at least '
            'one of the following: `links`, `data`, `meta`.'),
    }

    def to_internal_value(self, data):
        """
        Translate JSON API relationship representation to the ID DRF consumes.
        """
        if not set(data).intersection(self.MUST_HAVE_ONE_OF):
            self.fail('missing_must')

        value = super(
            JSONAPIRelationshipSerializer, self).to_internal_value(data)
        return self.fields['data'].get_attribute(value)

    def to_representation(self, value):
        """
        Translate the DRF related instances/IDs into the JSON API format.
        """
        instance = collections.OrderedDict()
        serializers.set_value(
            instance, self.fields['data'].source_attrs, value)
        serializers.set_value(
            instance, self.fields['links'].source_attrs, value)
        return super(JSONAPIRelationshipSerializer, self).to_representation(
            instance)


class JSONAPIResourceSerializer(
        JSONAPIPrimaryDataSerializer,
        JSONAPILinkableSerializer, JSONAPIMetaContainerSerializer):
    """
    Serializer for the JSON API specific aspects of a resource.
    """

    # In addition, a resource object MAY contain any of these top-level
    # members:
    attributes = serializers.DictField(
        label='Resource Attributes',
        help_text="an object representing some of the resource's data.",
        required=False, source='*')
    relationships = serializers.DictField(
        label='Related Resources',
        help_text='a relationships object describing relationships '
        'between the resource and other JSON API resources.',
        required=False, source='*', child=JSONAPIRelationshipSerializer())

    default_error_messages = {
        'reserved_field': (
            'A resource can not have {member!r} fields named: {fields}.'),
        'field_conflicts': (
            'A resource can not have `attributes` and `relationships` '
            'with the same name: {fields}.'),
        'id_field_in_attributes': (
            'A resource must not include the ID field in the attributes'),
    }

    primary = False

    json_api_reserved_fields = {'type', 'id'}
    field_inflectors = field_inflectors

    def __init__(
            self, instance=None, data=serializers.empty,
            field_inflectors=None, **kwargs):
        """
        Support specifying whether to use a flat URL string.
        """
        super(JSONAPIResourceSerializer, self).__init__(
            instance=instance, data=data, **kwargs)
        if field_inflectors is not None:
            self.field_inflectors = field_inflectors

    def to_internal_value(self, data):
        """
        Translate the JSON API format into the DRF internal format.
        """
        if isinstance(data, list):
            return super(
                JSONAPIResourceSerializer, self).to_internal_value(data)

        # De-inflect resource fields
        attributes = self.fields['attributes'].get_value(data)
        relationships = self.fields['relationships'].get_value(data)
        for field, resource_fields in (
                (self.fields['attributes'], attributes),
                (self.fields['relationships'], relationships)):
            try:
                field.run_validation(resource_fields)
            except (serializers.SkipField, exceptions.ValidationError):
                # Skip de-inflection if validation would fail
                continue
            for resource_field in resource_fields.keys():
                value = resource_fields.pop(resource_field)
                for inflector in self.field_inflectors:
                    resource_field = reverse_inflectors[inflector](
                        resource_field)
                resource_fields[resource_field] = value

        try:
            value = super(
                JSONAPIResourceSerializer, self).to_internal_value(data)
        except exceptions.APIException as exc:
            # Move resource field errors into attributes or relationships
            parameter_serializer = self.fields['type'].parameter_serializers[0]
            for field_name, field in parameter_serializer.child.fields.items():
                if field_name == self.fields['id'].source:
                    # Leave any ID field in the top-level
                    continue
                field_data = field.get_value(exc.detail)
                if field_data is serializers.empty:
                    # Skip fields not in the error
                    continue
                if isinstance(field, (
                        relations.RelatedField, relations.ManyRelatedField)):
                    exc.detail.setdefault(
                        'relationships', {})[field_name] = field_data
                else:
                    exc.detail.setdefault(
                        'attributes', {})[field_name] = field_data
                del exc.detail[field_name]
            raise exc

        # Do validation on original data but after normal validation to
        # include required and basic type validation
        errors = collections.OrderedDict()

        for member, jsonapi in (
                ('attributes', attributes), ('relationships', relationships)):
            if jsonapi is serializers.empty:
                continue
            reserved = self.json_api_reserved_fields.intersection(jsonapi)
            if reserved:
                try:
                    self.fail(
                        'reserved_field', member=member,
                        fields=', '.join(repr(field) for field in reserved))
                except exceptions.ValidationError as exc:
                    errors[member] = exc.detail
                    continue

        if serializers.empty not in [attributes, relationships]:
            conflicts = set(attributes).intersection(relationships)
            if conflicts:
                try:
                    self.fail('field_conflicts', fields=', '.join(repr(
                        field) for field in conflicts))
                except exceptions.ValidationError as exc:
                    errors["attributes"] = exc.detail

        if errors:
            raise exceptions.ValidationError(errors)

        return value

    def to_representation(self, instance):
        """
        Move the ID field out of the attributes.
        """
        # Need to handle resource fields manually to separate out related
        # fields.  Make sure the fields are bound and available in this scope
        # and then remove them from our schema before normal processing.
        fields = self.get_fields()
        attributes_field = self.fields.setdefault(
            'attributes', fields['attributes'])
        self.fields.pop('attributes', None)
        relationships_field = self.fields.setdefault(
            'relationships', fields['relationships'])
        self.fields.pop('relationships', None)

        data = super(JSONAPIResourceSerializer, self).to_representation(
            instance)
        if isinstance(data, list):
            return data

        parameter_serializer = self.fields['type'].parameter_serializers[0]
        attributes = collections.OrderedDict()
        relationships = collections.OrderedDict()
        for field_name, field in parameter_serializer.child.fields.items():
            if field_name == self.fields['id'].source:
                # Leave any ID field in the top-level
                continue
            if isinstance(field, (
                    relations.RelatedField, relations.ManyRelatedField)):
                fields = relationships
                try:
                    value = field.get_attribute(data.serializer.instance)
                except serializers.SkipField:
                    continue
            else:
                fields = attributes
                value = field.get_value(data)
                if value is serializers.empty:
                    continue
            data.pop(field_name, None)
            # Inflect the field name
            for inflector in self.field_inflectors:
                field_name = inflector(six.text_type(field_name))
            fields[field_name] = value
        if attributes:
            data['attributes'] = attributes_field.to_representation(
                attributes)
        if relationships:
            data['relationships'] = relationships_field.to_representation(
                relationships)

        return data


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
    status = serializers.CharField(
        label='Error Status',
        help_text='the HTTP status code applicable to this problem, '
        'expressed as a string value.',
        required=False)
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
            'A document may not contain `included` resources on '
            'incomming/write requrests: POST, PUT, PATCH, DELETE.'),
        'duplicate_resource': (
            'A document MUST NOT include more than one resource object '
            'for each type ({type!r}) and id ({id!r}) pair, '
            'duplicate found in {member!r}.'),
    }

    # A document MUST contain at least one of the following top-level members
    data = JSONAPIResourceSerializer(
        label='Resource', help_text='the document\'s "primary data"',
        # Can't use `source="*"` because primary data may be an array
        required=False)
    errors = serializers.ListField(
        label='Errors', help_text='an array of error objects',
        # Can't use `source="*"` because primary data may be an array
        required=False, read_only=True, child=JSONAPIErrorSerializer(
            label='Error', help_text='an error object'))

    # A document MAY contain any of these top-level members:
    jsonapi = JSONAPIImplementationSerializer(
        label='JSON API Implementation',
        help_text="an object describing the server's implementation",
        required=False, read_only=True, default={})
    included = serializers.ListField(
        label='Included Related Resources',
        help_text='an array of resource objects that are related '
        'to the primary data and/or each other ("included resources").',
        child=JSONAPIResourceSerializer(
            label='Included Related Resource',
            help_text='a resource object that is related to the primary data '
            'and/or other included resources/'),
        # Can't use `source="*"` because primary data may be an array
        required=False, read_only=True)

    def __init__(self, *args, **kwargs):
        """
        Set the `data` parameterized serializers as primary.
        """
        super(JSONAPIDocumentSerializer, self).__init__(*args, **kwargs)
        self.fields['data'].primary = True

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
        return self.fields['data'].get_attribute(value)

    def to_representation(self, instance):
        """
        Generate a JSON API document for the resource.
        """
        value = collections.OrderedDict()

        if isinstance(instance, exceptions.APIException):
            # Being used in the exception handler
            # Process a dict of errors into a JSON API array
            errors = [
                {
                    "status": instance.status_code,
                    "id": detail.code,
                    "source": {"pointer": source},
                    "title":  inflection.titleize(detail.code),
                    "detail": detail}
                for source, detail in flatten_error_details(instance.detail)]
            serializers.set_value(
                value, self.fields['errors'].source_attrs, errors)
        else:
            serializers.set_value(
                value, self.fields['data'].source_attrs, instance)

        data = super(JSONAPIDocumentSerializer, self).to_representation(value)

        # Do any post-processing validation
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

    def update(self, instance, validated_data):
        """
        Delegate to the primary data serializer
        """
        return validated_data.serializer.update(instance, validated_data)

    def create(self, validated_data):
        """
        Delegate to the primary data serializer
        """
        return validated_data.serializer.create(validated_data)

    def save(self, **kwargs):
        """
        Delegate to the primary data serializer
        """
        return self.validated_data.serializer.save(**kwargs)


pagination_links_serializer = JSONAPIPaginationLinksSerializer()
pagination_source_attrs = {
    field.source for field in pagination_links_serializer.fields.values()}
pagination_source_attrs.add('results')


class JSONAPIPaginationSerializer(
        JSONAPILinkableSerializer, JSONAPIMetaContainerSerializer):
    """
    Transform DRF's pagination data to the JSON API format.

    The schema is used only for documentation and introspection.  The actual
    representation is managed manually.
    """

    def to_representation(self, instance):
        """
        Reconstitute the JSON API format adding pagination links.
        """
        data = instance['results']

        # Supliment the links object with pagination data
        links = data.setdefault('links', collections.OrderedDict())
        for field_name, field in pagination_links_serializer.fields.items():
            try:
                links[field_name] = field.get_attribute(instance)
            except serializers.SkipField:
                links[field_name] = None

        # Move everything else into the meta object
        meta = data.setdefault('meta', collections.OrderedDict())
        meta['pagination'] = {
            key: value for key, value in instance.items()
            if key not in pagination_source_attrs}

        return data
