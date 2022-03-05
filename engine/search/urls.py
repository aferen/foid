from django.urls import include, path
from rest_framework import routers
from . import views

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('search', views.search),
    path('searchById', views.searchById),
    path('document/<str:docID>', views.getDocument),
    path('result/<str:docID>/<str:resultDocID>', views.getResultDocument)
]