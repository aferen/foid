from django.urls import path

from . import views
from documents import views as documentsViews

urlpatterns = [
  path('', documentsViews.search, name='index'),
  path('error', views.error, name='error')
]
