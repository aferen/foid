from django.db import models

class CustomManager(models.Manager):
    def get_queryset(self):
        query = super(models.Manager, self).get_queryset()
        return query

class Documents(models.Model):
    name = models.CharField(max_length=250)
    docID = models.UUIDField(editable=False, unique=True)
    metadata = models.TextField(null=True,  blank=True)
    path = models.TextField(null=True,blank=True)
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
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    objects = CustomManager()

    class Meta:
        managed = False
        db_table = "documents_searchhistory"

    def save(self, *args, **kwargs):
        super(SearchHistory, self).save(*args, **kwargs)