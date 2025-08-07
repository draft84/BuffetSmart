# mixins.py
# from dishes.schema import set_schema
# from django.db import transaction
# from contextlib import contextmanager
# from dishes.schema import set_schema
# from dishes.utils import schema_context
# from .models import Logs
# from rest_framework.request import Request

# class SchemaMixin:
#     def dispatch(self, request, *args, **kwargs):
#         set_schema(request.user)
#         print(request.user)
#         return super().dispatch(request, *args, **kwargs)

#     def get_queryset(self):
#         with transaction.atomic():
#             set_schema(self.request.user)
#             return super().get_queryset()

#     def perform_create(self, serializer):
#         with transaction.atomic():
#             transaction.on_commit(lambda: set_schema(self.request.user))
#         super().perform_create(serializer)

#     def perform_update(self, serializer):
#         with transaction.atomic():
#             set_schema(self.request.user)
#             transaction.on_commit(lambda: set_schema(self.request.user))
#             print("Perform update: esquema establecido")
#         super().perform_update(serializer)

#     def perform_destroy(self, instance):
#         with transaction.atomic():
#             transaction.on_commit(lambda: set_schema(self.request.user))
#         super().perform_destroy(instance)


from django.db import transaction
from dishes.schema import set_schema
from dishes.utils import schema_context

class SchemaMixin:
    def dispatch(self, request, *args, **kwargs):
        with schema_context(request.user):
            return super().dispatch(request, *args, **kwargs)
        
    def get_queryset(self):
        with transaction.atomic():
            set_schema(self.request.user)
            return super().get_queryset()

    def perform_create(self, serializer):
        with schema_context(self.request.user):
            super().perform_create(serializer)

    def perform_update(self, serializer):
        with schema_context(self.request.user):
            super().perform_update(serializer)

    def perform_destroy(self, instance):
        with schema_context(self.request.user):
            super().perform_destroy(instance)
