from django.db import models
from user_management.models import Profile
from django.contrib.auth.models import User

class Message(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)