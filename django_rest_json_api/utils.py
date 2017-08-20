"""
Utilities used in parsing/rendering JSON API.
"""

import inflection


def to_kwargs(attributes):
    """
    Take JSON API attributes and return python kwargs.

    For example, convert dashes in keys to underscores.
    """
    return {
        inflection.underscore(key): value
        for key, value in attributes.items()}
