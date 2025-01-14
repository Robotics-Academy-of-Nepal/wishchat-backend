from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload'),
    path('delete/', views.delete_file, name='delete'),
]

