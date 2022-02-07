from django.urls import path

from . import views

urlpatterns = [
  path('', views.index, name='documents_index'),
  path('search', views.search, name='documents_search'), 
  path('search/<int:document_id>', views.searchById, name='documents_searchById'),  
  path('detail/<int:document_id>', views.detail, name='documents_detail'),
  path('delete/<int:document_id>', views.delete, name='documents_delete'),
  path('deleteHistory/<int:history_id>', views.deleteSearchHistory, name='documents_deleteSearchHistory')
]