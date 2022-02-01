from django.urls import path

from . import views

urlpatterns = [
  path('', views.index, name='documents_index'),
  path('search', views.search, name='search'),
]