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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    docID = models.UUIDField(default=generate_uuid, editable=False, unique=True)
    metadata = models.TextField(null=True,  blank=True)
    path = models.FileField(upload_to=get_file_path,null=True,blank=True,)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(Documents, self).save(*args, **kwargs)


class SearchHistory(models.Model):
    document = models.ForeignKey(Documents, on_delete=models.CASCADE)
    query = models.CharField(null=True,  blank=True, max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(SearchHistory, self).save(*args, **kwargs)