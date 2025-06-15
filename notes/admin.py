from django.contrib import admin
from .models import Note  # Importáljuk a Note modellt

admin.site.register(Note)  # Regisztráljuk az admin felületen