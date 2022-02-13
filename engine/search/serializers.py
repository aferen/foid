from rest_framework import serializers

from .models import Documents
from django.db import models

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Documents
        fields = ('docID',)