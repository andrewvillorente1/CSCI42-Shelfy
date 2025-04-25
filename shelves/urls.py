from django.urls import path
from .views import UserShelvesView, PublicShelfView, AddToShelfView, RemoveFromShelfView, ShelfItemDetailView


app_name = 'shelves'

urlpatterns = [
    path('', UserShelvesView.as_view(), name='user_shelves'),
    path('add/', AddToShelfView.as_view(), name='add_to_shelf'),
    path('remove/', RemoveFromShelfView.as_view(), name='remove_from_shelf'),
    path('<str:username>/', PublicShelfView.as_view(), name='public_shelf'),
    path('<str:username>/item/<int:item_id>/',
         ShelfItemDetailView.as_view(), name='shelf_item_detail'),
]
