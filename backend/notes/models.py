from django.db import models
from django.contrib.auth.models import User

class Board(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    position_x = models.IntegerField(default=100)
    position_y = models.IntegerField(default=100)
    emoji = models.CharField(max_length=2, default="📄")


    def __str__(self):
        return self.title

class Note(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    position_x = models.IntegerField(default=100)
    position_y = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    background_color = models.CharField(max_length=20, default="#fff8b3")
    text_color = models.CharField(max_length=20, default="#000000")
    width = models.IntegerField(default=160)
    height = models.IntegerField(default=100)

class Document(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

