from django.db import models, connections
from rest_framework.authentication import BasicAuthentication
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from api.serializers import TableSerializer, DynamicModelSerializer
from api.models import UserTable, BaseModel

class DynamicModelViewSet(viewsets.GenericViewSet):

    @property
    def model(self):
        mdl = None
        pk = self.kwargs['user_table_pk']
        if UserTable.objects.filter(user=self.request.user.id, id=pk).exists():
            ut = UserTable.objects.filter(user=self.request.user.id, id=pk).get()
            attrs = {'__module__': __name__}
            for field in ut.fields:
                match field['type']:
                    case 'number': attrs[field['name']] = models.IntegerField(field['title'], null=True)
                    case 'boolean': attrs[field['name']] = models.BooleanField(field['title'], null=True)
                    case _: attrs[field['name']] = models.CharField(field['title'], max_length=255, blank=True)
            mdl = type(ut.name, (BaseModel,), attrs)
        print(mdl)
        return mdl

    def get_queryset(self):
        model = self.model
        return model.objects.all()           

    def get_serializer_class(self):
        # Check if the model is dynamically set
        if hasattr(self, 'model') and self.model is not None:
            # Create a dynamic serializer with the model
            serializer_class = type(
                f'{self.model.__name__}Serializer',
                (DynamicModelSerializer,),
                {'Meta': type('Meta', (), {'model': self.model, 'fields': '__all__'})}
            )
            return serializer_class
        
        # If the model is not set, use the default serializer
        return super().get_serializer_class()

class CreateDynamicModeViewSet(mixins.CreateModelMixin, DynamicModelViewSet):
    pass

class ListDynamicModeViewSet(mixins.ListModelMixin, DynamicModelViewSet):
    pass

class TableView(#mixins.RetrieveModelMixin, # uncomment this mixin to enable GET detail method
                #mixins.ListModelMixin, # uncomment this mixin to enable GET list method
                mixins.CreateModelMixin,
                mixins.UpdateModelMixin,
                viewsets.GenericViewSet):
    serializer_class = TableSerializer
    queryset = UserTable.objects.all()

    def get_queryset(self):
       return UserTable.objects.filter(user=self.request.user.id)

    def get_user_model(self, table_name, table_fields):
        attrs = {'__module__': __name__}
        for field in table_fields:
            match field['type']:
                case 'number': attrs[field['name']] = models.IntegerField(field['title'], null=True)
                case 'boolean': attrs[field['name']] = models.BooleanField(field['title'], null=True)
                case _: attrs[field['name']] = models.CharField(field['title'], max_length=255, blank=True)
        model = type(table_name, (BaseModel,), attrs)
        return model
    
    def create_user_model(self, table_name, table_fields):
        model = self.get_user_model(table_name, table_fields)
        connection = connections['default']
        with connection.schema_editor() as editor:
            editor.create_model(model)

    def delete_user_model(self, table_name, table_fields):
        model = self.get_user_model(table_name, table_fields)
        connection = connections['default']
        with connection.schema_editor() as editor:
            editor.delete_model(model)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        self.create_user_model(serializer.data['name'], serializer.data['fields'])


    def perform_update(self, serializer):
        instance = self.get_object()
        self.delete_user_model(instance.name, instance.fields)
        serializer.save(user=self.request.user)
        self.create_user_model(serializer.data['name'], serializer.data['fields'])

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}
        
    @authentication_classes([BasicAuthentication])
    @permission_classes([IsAuthenticated])
    def create(self, request, *args, **kwargs):
        serializer = TableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @authentication_classes([BasicAuthentication])
    @permission_classes([IsAuthenticated])
    def update(self, request, pk=None, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = TableSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
