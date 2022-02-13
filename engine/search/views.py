from django.shortcuts import render

from rest_framework import status
from .serializers import DocumentSerializer
from .models import Documents, SearchHistory
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q


@api_view(['POST'])
def search(request):
    if request.method == 'POST':
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            docID = request.data['docID']
            document = Documents.objects.get(Q(docID=docID))
            if document:
                searchHistory = SearchHistory.objects.filter(Q(document=document)).order_by('pk').last()
                docPath = document.path
                findObject(docPath)
                query = searchHistory.query
                serializer = DocumentSerializer(document)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def findObject(docPath):
    print(docPath)