from django.urls import path

from . import views

urlpatterns = [
  path('add', views.add, name='addobject'),
  path('addAllObject', views.saveAllObject, name='addAllObject'),
  path('edit/<int:object_id>', views.edit, name='editobject'),
  path('delete/<int:object_id>', views.delete, name='deleteobject'),
  path('', views.index, name='object_index')
]
