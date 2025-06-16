from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Felhasználóhoz kapcsolás

    def __str__(self):
        return self.title
        
class Document(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='uploads/')  # Ide kerülnek a fájlok

class Board(models.Model):
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)