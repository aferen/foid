from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('pages.urls')),
    path('users/', include('users.urls')),
    path('documents/', include('documents.urls')),
    path('objects/', include('objects.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
