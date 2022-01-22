from django.urls import path

from . import views

urlpatterns = [
  path('login', views.login, name='login'),
  path('logout', views.logout, name='logout'),
  path('register', views.register, name='register'),
  path('edituser/<int:user_id>', views.edituser, name='edituser'),
  path('profile', views.profile, name='profile'),
  path('deleteuser/<int:user_id>', views.deleteuser, name='deleteuser'),
  path('', views.index, name='user_index')
]
