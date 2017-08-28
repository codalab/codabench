from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView


# class SearchAPIView(APIView):
#
#     def get(self, request):
#         client = Elasticsearch()
#         s = Search(using=client)
#
#         # Do filters
#         if 'q' in request.GET:
#             s = s.query("match", title=request.GET['q'])
#
#         # Get results
#         results = s.execute()
#         data = []
#         for result in results:
#             # print(result)
#             data.append({key: result[key] for key in result})
#
#         return Response(data)



@api_view(['GET'])
def query(request):
    client = Elasticsearch()
    s = Search(using=client)

    # Do filters
    if 'q' in request.GET:
        s = s.query("match", title=request.GET['q'])

    # Get results
    results = s.execute()
    data = []
    for result in results:
        # print(result)
        data.append({key: result[key] for key in result})

    return Response(data)


# class SearchAPIView(RetrieveAPIView):
#     def get(self, request, format=None):
#         client = Elasticsearch()
#         s = Search(using=client)
#         results = s.execute()
#
#         data = []
#
#         for result in results:
#             print(result['created_by'])
#             data.append({key: result[key] for key in result})
#
#         return Response(data)
