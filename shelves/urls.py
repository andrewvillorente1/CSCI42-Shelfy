from django.urls import path
from . import views

app_name = 'shelves'

urlpatterns = [
    path('', views.user_shelves, name='user_shelves'),
    path('add/', views.add_to_shelf, name='add_to_shelf'),
    path('remove/', views.remove_from_shelf, name='remove_from_shelf'),
    path('user/<str:username>/', views.public_shelf, name='public_shelf'),
    path('user/<str:username>/item/<int:item_id>/',
         views.shelf_item_detail, name='shelf_item_detail'),
]
