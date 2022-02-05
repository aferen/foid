# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from users.models import User

class CustomManager(models.Manager):
    def get_queryset(self):
        query = super(models.Manager, self).get_queryset()
        return query

class Documents(models.Model):
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    metadata = models.TextField(null=True,  blank=True)
    path = models.FileField(upload_to='static/')
    query = models.CharField(null=True,  blank=True, max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(Documents, self).save(*args, **kwargs)

class SearchHistory(models.Model):
    documentID = models.ForeignKey(Documents, on_delete=models.CASCADE, verbose_name='doküman')
    query = models.CharField('arama cümlesi', null=True,  blank=True, max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(SearchHistory, self).save(*args, **kwargs)

