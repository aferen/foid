from django.urls import path

from . import views

urlpatterns = [
  path('adddocuments', views.adddocuments, name='adddocuments'),
  path('', views.index, name='documents_index'),
  path('<int:documents_id>', views.documents, name='documents'),
  path('delete_documents/<int:documents_id>', views.deletedocuments, name='delete_documents'),
  path('documents_details/<int:documents_id>', views.documentsDetails, name='documents_details'),
  path('first_search', views.firstsearch, name='first_search'),
  path('second_search', views.secondsearch, name='second_search'),
]