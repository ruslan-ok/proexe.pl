from jsonschema import validate
from django.db import models
from rest_framework import serializers
from api.models import UserTable

class DynamicModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = '__all__'
        
class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTable
        fields = ['id', 'name', 'fields']

    def validate_name(self, value):
        if not value.isidentifier():
            raise serializers.ValidationError('This field must be a valid identifier.')
        else:
            if value == 'usertable' or (not self.instance and UserTable.objects.filter(name=value).exists()):
                raise serializers.ValidationError(f'User table with name {value} already exists.')
            return value
    
    def validate_fields(self, value):
        schema = {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'type': {'type': 'string'},
                    'title': {'type': 'string'},
                },
                'required': ['name', 'type', 'title'],
            }
        }
        try:
            validate(instance=value, schema=schema)
        except:
            raise serializers.ValidationError('This field must be a non-empty array of objects with attributes "name", "type" and "title".')

        if not len(value):
            raise serializers.ValidationError('This field must be a non-empty array of objects with attributes "name", "type" and "title".')

        for x in value:
            if not x['name'].isidentifier():
                raise serializers.ValidationError('Attribute "name" must be a valid identifier.')
            if x['type'] not in ('string', 'number', 'boolean'):
                raise serializers.ValidationError('Valid values for the "type" attribute are "string", "number" or "boolean".')
            if not x['title']:
                raise serializers.ValidationError('Valid for the "title" attribute must be not empty string.')
        return value

class TableRowSerializer(serializers.Serializer):
    row = serializers.JSONField()