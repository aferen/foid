from django.db import migrations, models
from django.contrib.auth.models import AbstractUser, UserManager


class User(AbstractUser):
    is_admin = models.BooleanField('isAdmin', default=False)

    objects = UserManager()

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

