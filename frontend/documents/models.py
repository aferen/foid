# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from users.models import User    
import uuid
import os

def generate_uuid():
    return uuid.uuid4().hex

def get_file_path(instance, filename):
    filename = "%s.%s" % (instance.docID, filename.split('.')[-1])
    return os.path.join('static/', filename)

class CustomManager(models.Manager):
    def get_queryset(self):
        query = super(models.Manager, self).get_queryset()
        return query

class Documents(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    name = models.CharField(max_length=250)
    docID = models.UUIDField(default=generate_uuid, editable=False, unique=True)
    docPath = models.TextField(null=True,blank=True)
    metadataID = models.UUIDField(null=True,  blank=True)
    metadataPath = models.TextField(null=True,  blank=True)
    eof = models.BooleanField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(Documents, self).save(*args, **kwargs)


class SearchHistory(models.Model):
    document = models.ForeignKey(Documents, on_delete=models.CASCADE)
    query = models.CharField(null=True,  blank=True, max_length=200)
    resultDocID = models.UUIDField(null=True,  blank=True)
    resultDocPath = models.TextField(null=True,  blank=True)
    resultTotalObject = models.IntegerField(null=True,  blank=True)
    resultTotalImage = models.IntegerField(null=True,  blank=True)
    resultTotalPage = models.IntegerField(null=True,  blank=True)
    resultPageList = models.TextField(null=True,  blank=True)
    resultMessage = models.TextField(null=True,  blank=True, max_length=250)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(SearchHistory, self).save(*args, **kwargs)