from rest_framework.generics import RetrieveAPIView, ListAPIView, DestroyAPIView, CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers import data as serializers
from datasets.models import Data, DataGroup


# class DataViewSetCreate(CreateAPIView, GenericViewSet):
#     queryset = Data.objects.all()
#     serializer_class = serializers.DataSerializer
#     parser_classes = (MultiPartParser,)
#
#     # def put(self, request, filename, format=None):
#     #     file_obj = request.data['file']
#     #     # ...
#     #     # do some stuff with uploaded file
#     #     # ...
#     #     return Response(status=204)
#     def perform_create(self, serializer):
#         serializer.save(
#             owner=self.request.user,
#             data_file=self.request.data.get('data_file')
#         )


class DataViewSet(ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView, GenericViewSet):
    queryset = Data.objects.all()
    serializer_class = serializers.DataSerializer
    parser_classes = (MultiPartParser,)
    permission_classes = (IsAuthenticated,)

    # def get_serializer(self, *args, **kwargs):
    #     if self.request.method == 'POST':
    #         return serializers.DataSerializer
    #     else:
    #         return serializers.DataSerializer

    # def put(self, *args, **kwargs):
    #     return self.put()
    # def post(self, request, *args, **kwargs):
    #     # MultiPartParser
    #     pass
    # def perform_create(self, serializer):
    #     serializer.save(
    #         owner=self.request.user,
    #         data_file=self.request.data.get('data_file')
    #     )


class DataGroupViewSet(ModelViewSet):
    queryset = DataGroup.objects.all()
    serializer_class = serializers.DataGroupSerializer
