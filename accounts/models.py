# accounts/models.py 
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    favorite_team = models.CharField(max_length=100, blank=True, null=True)
