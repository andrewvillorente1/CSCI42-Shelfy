from django.urls import path
from . import views

app_name = 'socials'

urlpatterns = [
    # path('lobby/', views.lobby, name='lobby'), #to remove
    path('', views.chat, name='chat'),
    path('create-message/', views.create_message, name='create-message'),
    path('stream-chat-messages/', views.stream_chat_messages, name='stream-chat-messages'),
]