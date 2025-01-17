# users/urls.py

from django.urls import path
from . import views


app_name = 'users'

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
]
