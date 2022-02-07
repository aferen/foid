from django.urls import path

from . import views

urlpatterns = [
  path('login', views.login, name='login'),
  path('logout', views.logout, name='logout'),
  path('register', views.register, name='register'),
  path('add', views.add, name='adduser'),
  path('edit/<int:user_id>', views.edit, name='edituser'),
  path('profile', views.profile, name='profile'),
  path('delete/<int:user_id>', views.delete, name='deleteuser'),
  path('', views.index, name='user_index')
]
