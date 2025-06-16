from django.shortcuts import render
from rest_framework import viewsets
from .models import Note
from .serializers import NoteSerializer
from rest_framework import permissions
from .models import Board
from .serializers import BoardSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Document
from .serializers import DocumentSerializer



class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()  # Itt definiáljuk a querysetet
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]  # Csak bejelentkezett felhasználók

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)  # Csak saját jegyzetek

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Automatikusan hozzárendeli a felhasználót

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Az aktuális felhasználóhoz kötött board