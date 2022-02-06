from django.urls import path

from . import views

urlpatterns = [
  path('', views.index, name='documents_index'),
  path('search', views.search, name='documents_search'),  
  path('detail/<int:thesis_id>', views.detail, name='documents_detail'),
  path('delete/<int:thesis_id>', views.delete, name='documents_delete')
 
]