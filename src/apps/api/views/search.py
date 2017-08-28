from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def query(request):
    client = Elasticsearch([settings.])
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
