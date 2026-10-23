from django.db import models
from django.conf import settings


class Cat(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cats', null=True, blank=True,
    )
    name = models.CharField(max_length=16)
    color = models.CharField(max_length=16)
    birth_year = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name
