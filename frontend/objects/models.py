from django.db import models


class CustomManager(models.Manager):
    def get_queryset(self):
        query = super(models.Manager, self).get_queryset()
        return query

class Objects(models.Model):
    objectID= models.IntegerField(null=False,blank=False)
    nameEN = models.CharField(max_length=250,null=False,blank=False)
    nameTR = models.CharField(max_length=250,null=False,blank=False)
    color = models.CharField(max_length=20,null=False,blank=False)
    objects = CustomManager()

    def save(self, *args, **kwargs):
        super(Objects, self).save(*args, **kwargs)
