from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chatbot_view, name='process_chat_query'),
    path('message-usage/', views.get_message_usage, name='message-usage'),
    path('1dfb88d7-85fb-4e62-ba34-2446150ad8e5', views.whatsAppWebhook, name='whatsapp_webhook'),
]