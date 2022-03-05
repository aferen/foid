from django.db import models
import uuid


def generate_uuid():
    return uuid.uuid4().hex

class CustomManager(models.Manager):
    def get_queryset(self):
        query = super(models.Manager, self).get_queryset()
        return query

class Documents(models.Model):
    name = models.CharField(max_length=250)
    docID = models.UUIDField(default=generate_uuid, editable=False, unique=True)
    docPath = models.TextField(null=True,blank=True)
    metadataID = models.UUIDField(null=True,  blank=True)
    metadataPath = models.TextField(null=True,  blank=True)
    eof = models.BooleanField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    class Meta:
        managed = False
        db_table = "documents_documents"

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

    class Meta:
        managed = False
        db_table = "documents_searchhistory"

    def save(self, *args, **kwargs):
        super(SearchHistory, self).save(*args, **kwargs)


class Result(models.Model):
    def __init__(self, docID, docPath,totalObject, totalImage, totalPage, pageList, message): 
        self.docID = docID
        self.docPath = docPath
        self.totalObject = totalObject
        self.totalImage = totalImage
        self.totalPage = totalPage
        self.pageList = pageList
        self.message = message

