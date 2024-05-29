from django.contrib.auth.models import AbstractUser
from django.db import models

from helpers.models import BaseModel


class User(AbstractUser, BaseModel):
    name = models.CharField(max_length=100)
