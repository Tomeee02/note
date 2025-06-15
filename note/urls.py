from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notes.views import NoteViewSet
from django.contrib import admin
from django.urls import path

router = DefaultRouter()
router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),  # Ez kell az admin felülethez
]
