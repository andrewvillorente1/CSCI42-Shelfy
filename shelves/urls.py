from django.urls import path
from .views import UserShelvesView, PublicShelfView, AddToShelfView, RemoveFromShelfView, ShelfItemDetailView


app_name = 'shelves'

urlpatterns = [
    path('', UserShelvesView.as_view(), name='user_shelves'),
    path('add/', AddToShelfView.as_view(), name='add_to_shelf'),
    path('<str:username>/<int:shelf_id>', PublicShelfView.as_view(), name='public_shelf'),
    path('<str:username>/<int:shelf_id>/<int:item_id>/', ShelfItemDetailView.as_view(), name='shelf_detail'),
    path('<int:shelf_id>/remove/<int:item_id>/', RemoveFromShelfView.as_view(), name='remove_from_shelf'),
]