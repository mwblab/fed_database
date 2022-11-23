from django.db import models
from django.utils import timezone

class Test(models.Model):
    name = models.CharField(max_length=255)  

