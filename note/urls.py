from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notes.views import NoteViewSet
from django.contrib import admin
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from notes.views import BoardViewSet  # A "notes" alkalmazásból kell importálni!
from notes.views import DocumentViewSet  # 📌 Ezt kell hozzáadni!





router = DefaultRouter()
router.register(r'notes', NoteViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'boards', BoardViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),  # Ez kell az admin felülethez
    path('api/auth/', obtain_auth_token),  # Bejelentkezés végpont
]
urlpatterns += router.urls