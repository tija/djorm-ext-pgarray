# -*- coding: utf-8 -*-
from django import forms
from django.db import models
from django.utils.encoding import force_unicode
from .utils import parse_array, edit_string_for_array


class ArrayWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, basestring):
            value = edit_string_for_array(value)
        return super(ArrayWidget, self).render(name, value, attrs)


def _cast_to_unicode(data):
    if isinstance(data, (list, tuple)):
        return [_cast_to_unicode(x) for x in data]
    elif isinstance(data, str):
        return force_unicode(data)
    return data


class ArrayField(models.Field):
    __metaclass__ = models.SubfieldBase
    widget = ArrayWidget

    def __init__(self, *args, **kwargs):
        self._array_type = kwargs.pop('dbtype', 'int')
        self._dimension = kwargs.pop('dimension', 1)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('null', True)
        kwargs.setdefault('default', None)
        super(ArrayField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return '{0}{1}'.format(self._array_type, "[]" * self._dimension)

    def get_db_prep_value(self, value, connection, prepared=False):
        value = value if prepared else self.get_prep_value(value)
        if not value or isinstance(value, basestring):
            return value

        return value

    def get_prep_value(self, value):
        return value

    def to_python(self, value):
        return _cast_to_unicode(value)
    
    def clean(self, value, model_instance):
        value = super(ArrayField, self).clean(value, model_instance)
        try:
            return parse_array(value)
        except ValueError:
            raise forms.ValidationError(_("Please provide a comma-separated list of values."))



# South support
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([
        (
            [ArrayField], # class
            [], # positional params
            {
                "dbtype": ["_array_type", {"default": "int"}],
                "dimension": ["_dimension", {"default": 1}],
            }
        )
    ], ['^djorm_pgarray\.fields\.ArrayField'])
except ImportError:
    pass