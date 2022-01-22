from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class User(AbstractUser):
    is_admin = models.BooleanField('admin mi?', default=False)

    objects = UserManager()

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)