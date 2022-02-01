# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from users.models import User

class CustomManager(models.Manager):
    def get_queryset(self):
        query = super(models.Manager, self).get_queryset()
        return query

class Documents(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=u'yükleyen kullanici')
    documents_name = models.CharField('doküman ismi', unique=True, max_length=250)
    documents_metadata = models.TextField('doküman metadata', null=True,  blank=True)
    documents_doc = models.FileField('yüklenen doküman', upload_to='static/')
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(Documents, self).save(*args, **kwargs)

class SearchHistory(models.Model):
    SearchHistory_documents = models.ForeignKey(Documents, on_delete=models.CASCADE, verbose_name='doküman')
    search_sentence = models.CharField('arama cümlesi', null=True,  blank=True, max_length=200)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(SearchHistory, self).save(*args, **kwargs)

