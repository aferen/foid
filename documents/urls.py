from django.urls import path

from . import views

urlpatterns = [
  path('', views.index, name='documents_index'),
  path('search', views.search, name='documents_search'),  
  path('detail/<int:document_id>', views.detail, name='documents_detail'),
  path('delete/<int:document_id>', views.delete, name='documents_delete')
 
]