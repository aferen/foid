from rest_framework import serializers

from .models import Documents, SearchHistory
from django.db import models

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Documents
        fields = ('docID',)

class ResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ('resultDocID',)