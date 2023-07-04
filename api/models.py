from django.db import models
from django.contrib.auth.models import User
from rest_framework import serializers

class UserTable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='user', related_name = 'table_user')
    name = models.CharField('Table name', max_length=200, blank=False)
    fields = models.JSONField('Fields', null=False)

class BaseModel(models.Model):
    class Meta:
         abstract = True # define abstract so that it does not cause any problem with model hierarchy in database

    @classmethod
    def get_serializer(cls):
         class BaseSerializer(serializers.ModelSerializer):
               class Meta:
                    model = cls # this is the main trick here, this is how I tell the serializer about the model class

         return BaseSerializer
    

