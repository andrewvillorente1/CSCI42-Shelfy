from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Shelf, ShelfItem
from user_library.models import UserLibraryItem


@login_required
def user_shelves(request):
    """
    View for managing a user's shelves.
    Each user has one default shelf for now.
    """
    # Handle the case where a user might have multiple shelves
    shelves = Shelf.objects.filter(user=request.user)

    if shelves.count() > 1:
        # Keep the first shelf and merge items from other shelves
        primary_shelf = shelves.first()
        with transaction.atomic():
            for shelf in shelves.exclude(id=primary_shelf.id):
                # Move items from other shelves to the primary shelf
                for item in ShelfItem.objects.filter(shelf=shelf):
                    # Only add if not already on the primary shelf
                    if not ShelfItem.objects.filter(shelf=primary_shelf, item=item.item).exists():
                        ShelfItem.objects.create(
                            shelf=primary_shelf, item=item.item)
                # Delete the extra shelf
                shelf.delete()

        messages.info(request, "We've consolidated your shelves into one.")
        shelf = primary_shelf
    elif shelves.count() == 1:
        shelf = shelves.first()
    else:
        # Create a new shelf if none exists
        shelf = Shelf.objects.create(user=request.user)

    # Handle form submission to update shelf settings
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        if name:
            shelf.name = name
            shelf.description = description
            shelf.save()
            messages.success(request, "Your shelf has been updated!")
        else:
            messages.error(request, "Shelf name cannot be empty.")

        return redirect('shelves:user_shelves')

    # Get all library items that are not already on the shelf
    library_items = UserLibraryItem.objects.filter(user=request.user)

    # Get all shelf items
    shelf_items = ShelfItem.objects.filter(shelf=shelf)

    # Get IDs of items already on the shelf
    shelf_item_ids = shelf_items.values_list('item_id', flat=True)

    # Filter library items to exclude those already on the shelf
    available_library_items = library_items.exclude(id__in=shelf_item_ids)

    context = {
        'shelf': shelf,
        'shelf_items': shelf_items,
        'library_items': available_library_items,
    }

    return render(request, 'shelves/user_shelves.html', context)


@login_required
@require_POST
def add_to_shelf(request):
    """
    Add a library item to the user's shelf.
    """
    item_id = request.POST.get('item_id')

    if not item_id:
        messages.error(request, "No item selected.")
        return redirect('shelves:user_shelves')

    # Handle the case where a user might have multiple shelves
    shelves = Shelf.objects.filter(user=request.user)

    if shelves.count() > 1:
        # Keep the first shelf and merge items from other shelves
        primary_shelf = shelves.first()
        with transaction.atomic():
            for shelf in shelves.exclude(id=primary_shelf.id):
                # Move items from other shelves to the primary shelf
                for item in ShelfItem.objects.filter(shelf=shelf):
                    # Only add if not already on the primary shelf
                    if not ShelfItem.objects.filter(shelf=primary_shelf, item=item.item).exists():
                        ShelfItem.objects.create(
                            shelf=primary_shelf, item=item.item)
                # Delete the extra shelf
                shelf.delete()

        shelf = primary_shelf
    elif shelves.count() == 1:
        shelf = shelves.first()
    else:
        # Create a new shelf if none exists
        shelf = Shelf.objects.create(user=request.user)

    # Get the library item
    try:
        library_item = UserLibraryItem.objects.get(
            id=item_id, user=request.user)
    except UserLibraryItem.DoesNotExist:
        messages.error(request, "Item not found in your library.")
        return redirect('shelves:user_shelves')

    # Check if the item is already on the shelf
    if ShelfItem.objects.filter(shelf=shelf, item=library_item).exists():
        messages.info(
            request, f"'{library_item.media.title}' is already on your shelf.")
    else:
        # Add the item to the shelf
        ShelfItem.objects.create(shelf=shelf, item=library_item)
        messages.success(
            request, f"'{library_item.media.title}' added to your shelf!")

    return redirect('shelves:user_shelves')


@login_required
@require_POST
def remove_from_shelf(request):
    """
    Remove a library item from the user's shelf.
    """
    item_id = request.POST.get('item_id')

    if not item_id:
        messages.error(request, "No item selected.")
        return redirect('shelves:user_shelves')

    # Handle the case where a user might have multiple shelves
    shelves = Shelf.objects.filter(user=request.user)

    if shelves.count() > 1:
        # Keep the first shelf and merge items from other shelves
        primary_shelf = shelves.first()
        with transaction.atomic():
            for shelf in shelves.exclude(id=primary_shelf.id):
                # Move items from other shelves to the primary shelf
                for item in ShelfItem.objects.filter(shelf=shelf):
                    # Only add if not already on the primary shelf
                    if not ShelfItem.objects.filter(shelf=primary_shelf, item=item.item).exists():
                        ShelfItem.objects.create(
                            shelf=primary_shelf, item=item.item)
                # Delete the extra shelf
                shelf.delete()

        shelf = primary_shelf
    elif shelves.count() == 1:
        shelf = shelves.first()
    else:
        messages.error(request, "You don't have a shelf yet.")
        return redirect('shelves:user_shelves')

    # Get the library item
    try:
        library_item = UserLibraryItem.objects.get(
            id=item_id, user=request.user)
    except UserLibraryItem.DoesNotExist:
        messages.error(request, "Item not found in your library.")
        return redirect('shelves:user_shelves')

    # Remove the item from the shelf
    try:
        shelf_item = ShelfItem.objects.get(shelf=shelf, item=library_item)
        shelf_item.delete()
        messages.success(
            request, f"'{library_item.media.title}' removed from your shelf.")
    except ShelfItem.DoesNotExist:
        messages.error(request, "Item not found on your shelf.")

    return redirect('shelves:user_shelves')


def public_shelf(request, username):
    """
    View a user's public shelf.
    """
    # Get the user
    user = get_object_or_404(User, username=username)

    # Handle the case where a user might have multiple shelves
    shelves = Shelf.objects.filter(user=user)

    if shelves.count() > 0:
        # Just use the first shelf for public viewing
        shelf = shelves.first()
    else:
        raise Http404("This user doesn't have a public shelf.")

    # Get all items on the shelf
    items = ShelfItem.objects.filter(shelf=shelf)

    context = {
        'shelf': shelf,
        'items': items,
        'shelf_owner': user,
    }

    return render(request, 'shelves/public_shelf.html', context)


def shelf_item_detail(request, username, item_id):
    """
    View details of a specific item on a user's shelf.
    """
    # Get the user
    user = get_object_or_404(User, username=username)

    # Handle the case where a user might have multiple shelves
    shelves = Shelf.objects.filter(user=user)

    if shelves.count() > 0:
        # Just use the first shelf for public viewing
        shelf = shelves.first()
    else:
        raise Http404("This user doesn't have a public shelf.")

    # Get the library item
    library_item = get_object_or_404(UserLibraryItem, id=item_id)

    # Get the shelf item
    shelf_item = get_object_or_404(ShelfItem, shelf=shelf, item=library_item)

    # Get the media
    media = library_item.media

    context = {
        'shelf_item': shelf_item,
        'library_item': library_item,
        'media': media,
        'shelf_owner': user,
    }

    return render(request, 'shelves/shelf_item_detail.html', context)
