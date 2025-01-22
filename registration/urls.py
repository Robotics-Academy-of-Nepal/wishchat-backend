from django.urls import path
from .views import RegisterView, LoginView , LogoutView, UserProfileView, GoogleLoginView, CompanyView, WhatsappView
from . import views

urlpatterns = [  
    path('register/', RegisterView.as_view(), name='register'),  
    path('login/', LoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'), 
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('update-company/', CompanyView.as_view(), name='update-company'),
    path('whatsapp-credentials/', WhatsappView.as_view(), name='whatsapp-credentials'),
]  
